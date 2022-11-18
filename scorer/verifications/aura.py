from arango import ArangoClient
import config
import os
import time

client = ArangoClient(hosts=config.ARANGO_SERVER)
system = client.db("_system")
snapshot = client.db("snapshot")

# Constants related to arangodump

AURA_SNAPSHOT_DIR = f"/tmp/aura"

# Constants related to Aura scores

ENERGY_TEAM = [
    "xqmMHQMnBdakxs3sXXjy7qVqPoXmhhwOt4c_z1tSPwM",
    "AsjAK5gJ68SMYvGfCAuROsMrJQ0_83ZS92xy94LlfIA",
]
STARTING_ENERGY = 10000000
HOPS = 4
FLAGGING_MULTIPLIER = 4
RATING_CUTOFF_HOURS = 72
ALLOWED_RATINGS_PER_CUTOFF = 18

# Aura levels

GOLD = 6000000
SILVER = 2000000
BRONZE = 1000


def verify(block):
    print("Verification: Aura")

    # Create collections if needed

    if not snapshot.has_collection("energy"):
        snapshot.create_collection("energy")

    if not snapshot.has_collection("energyNext"):
        snapshot.create_collection("energyNext")

    if not snapshot.has_collection("energyFlow"):
        energy_flow = snapshot.create_collection("energyFlow", edge=True)
        energy_flow.add_persistent_index(fields=["timestamp"])

    if not snapshot.has_collection("aura"):
        snapshot.create_collection("aura")

    if not snapshot.has_collection("energyTotals"):
        snapshot.create_collection("energyTotals")

    energy = snapshot.collection("energy")
    energy_next = snapshot.collection("energyNext")
    aura = snapshot.collection("aura")
    enegry_totals = snapshot.collection("energyTotals")

    # Clear collections

    energy.truncate()
    energy_next.truncate()
    aura.truncate()
    enegry_totals.truncate()

    # Initialize the energy

    snapshot.aql.execute(
        """
        for e in @energyTeam
            insert {
                _key: e,
                energy: @startingEnergy
            } in energy
    """,
        bind_vars={"energyTeam": ENERGY_TEAM, "startingEnergy": STARTING_ENERGY},
    )

    # Flow the energy

    timestamp = time.time() * 1000

    for i in range(HOPS):

        if i < HOPS - 1:
            snapshot.aql.execute(
                """
                for e in energy
                    let scale = sum (
                        for ea in energyAllocation
                            filter ea._from == e._id
                            return ea.allocation
                    )
                    for ea in energyAllocation
                        filter ea._from == e._id
                        let key = split(ea._to,'/',2)[1]
                        upsert { _key: key }
                        insert { _key: key, energy: e.energy * ea.allocation / scale }
                        update { energy: OLD.energy + e.energy * ea.allocation / scale }
                        in energyNext
            """
            )
        else:  # Store transfers on the last hop for data visualization
            snapshot.aql.execute(
                """
                for e in energy
                    let scale = sum (
                        for ea in energyAllocation
                            filter ea._from == e._id
                            return ea.allocation
                    )
                    for ea in energyAllocation
                        filter ea._from == e._id
                        let key = split(ea._to,'/',2)[1]
                        let energySent = e.energy * ea.allocation / scale
                        upsert { _key: key }
                        insert { _key: key, energy: energySent }
                        update { energy: OLD.energy + energySent }
                        in energyNext
                        insert { _from: ea._from, _to: ea._to, energy: energySent, timestamp: @timestamp }
                        in energyFlow
            """,
                bind_vars={"timestamp": timestamp},
            )

        # Clean up old energyFlow data
        #
        # Remove the rows with the middle timestamp from today (if it exists)
        # leaving only the most recent and least recent rows.

        snapshot.aql.execute(
            """
             let timesToday = (
                for ef in energyFlow
                    filter ef.timestamp < @timestamp
                    and ef.timestamp > @timestamp - 86400000
                    collect timestamp = ef.timestamp
                return { timestamp: timestamp }
            )

            for ef in energyFlow
                filter ef.timestamp == timesToday[1].timestamp
                remove ef in energyFlow
        """,
            bind_vars={"timestamp": timestamp},
        )

        energy.truncate()
        energy.rename("energyTemp")
        energy_next.rename("energy")
        energy.rename("energyNext")
        energy = snapshot.collection("energy")
        energy_next = snapshot.collection("energyNext")

    # Energy flow table is clean now
    # Use this data to compute the total energy flow to each Aura player.
    # we need to sum all row with the same _to and _timestamp to get total inflow energy

    snapshot.aql.execute(
        """
        for ef in energyFlow
            let key = split(ef._to,'/',2)[1]
            let inflow = sum (
                for eft in energyFlow
                    filter eft._to == key and eft.timestamp == ef.timestamp
                    return eft.energy
            )
            let outflow = sum (
                for eft in energyFlow
                    filter eft._from == key and eft.timestamp == ef.timestamp
                    return eft.energy
            )
            insert { _key: key, inflowEnergy: inflow, outflowEnergy: outflow, timestamp: ef.timestamp }
            in energyTotals
    """
    )

    # Compute Aura scores

    snapshot.aql.execute(
        """
        let ratingCutoff = date_subtract(date_now(), @ratingCutoffHours, "hours")
    
        for h in honesty
            filter h.honesty >= 1 OR h.honesty <= -1
            for e in energy
                filter e._id == h._from
                let recentRatings = count(
                    for ratings in honesty
                        filter h.modified > ratingCutoff
                        filter ratings._from == h._from
                        filter ratings.modified > ratingCutoff
                        return 1
                )
                let partialScore = e.energy * h.honesty
                    * (h.honesty < 0 ? @flaggingMultiplier : 1)
                    * @allowedRatings / max([ recentRatings , @allowedRatings])
                    
                collect subject = h._to
                aggregate score = sum(partialScore)
                
                insert {
                    _key: split(subject,'/',2)[1],
                    score: score
                } in aura
                
    """,
        bind_vars={
            "flaggingMultiplier": FLAGGING_MULTIPLIER,
            "ratingCutoffHours": RATING_CUTOFF_HOURS,
            "allowedRatings": ALLOWED_RATINGS_PER_CUTOFF,
        },
    )

    # Transfer the aura collection from snapshot to _system

    result = os.system(
        f'arangodump --overwrite true --compress-output false --server.password ""'
        f' --server.endpoint "tcp://{config.BN_ARANGO_HOST}:{config.BN_ARANGO_PORT}"'
        f" --output-directory {AURA_SNAPSHOT_DIR} --server.database snapshot --collection aura"
    )
    assert result == 0, "Aura: dumping aura collection failed."
    result = os.system(
        f'arangorestore --server.username "root" --server.password "" --server.endpoint'
        f' "tcp://{config.BN_ARANGO_HOST}:{config.BN_ARANGO_PORT}" --input-directory {AURA_SNAPSHOT_DIR}'
    )
    assert result == 0, "Aura: restoring aura collection failed."

    # Write the verifications

    system.aql.execute(
        """
        for a in aura
        let level =
            a.score > @gold ? "Gold" :
            a.score > @silver ? "Silver" :
            a.score > @bronze ? "Bronze" :
            a.score > 0 ? "Zero" : "Sus"
        insert {
            name: "Aura",
            user: a._key,
            block: @block,
            timestamp: date_now(),
            score: a.score,
            level: level
        } into verifications
    """,
        bind_vars={
            "gold": GOLD,
            "silver": SILVER,
            "bronze": BRONZE,
            "block": block,
        },
    )


if __name__ == "__main__":
    verify(0)
    print("Aura processing finished")
