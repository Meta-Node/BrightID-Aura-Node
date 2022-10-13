from arango import ArangoClient
import time
import utils
import config
import os

client = ArangoClient(hosts=config.ARANGO_SERVER)
system = client.db('_system')
snapshot = client.db('snapshot')

# Constants related to arangodump

AURA_SNAPSHOT_DIR = f'{config.SNAPSHOTS_PATH}/aura'

# Constants related to Aura scores

ENERGY_TEAM = [
    'xqmMHQMnBdakxs3sXXjy7qVqPoXmhhwOt4c_z1tSPwM',
    'AsjAK5gJ68SMYvGfCAuROsMrJQ0_83ZS92xy94LlfIA',
]
STARTING_ENERGY = 10000000
HOPS = 4
FLAGGING_MULTIPLIER = 4
RATING_CUTOFF_HOURS = 72
ALLOWED_RATINGS_PER_CUTOFF = 18


def verify(block):
    print('Verification: Aura')

    # Create collections if needed

    if not snapshot.has_collection('energy'):
        snapshot.create_collection('energy')

    if not snapshot.has_collection('energyNext'):
        snapshot.create_collection('energyNext')

    if not snapshot.has_collection('aura'):
        snapshot.create_collection('aura')

    energy = snapshot.collection('energy')
    energy_next = snapshot.collection('energyNext')
    aura = snapshot.collection('aura')

    # Clear collections

    energy.truncate()
    energy_next.truncate()
    aura.truncate()

    # Initialize the energy

    snapshot.aql.execute('''
        for e in @energyTeam
            insert {
                _key: e,
                energy: @startingEnergy
            } in energy
    ''', bind_vars={
        "energyTeam": ENERGY_TEAM,
        "startingEnergy": STARTING_ENERGY
    })

    # Flow the energy

    for i in range(HOPS):
        snapshot.aql.execute('''
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
        ''')

        energy.truncate()
        energy.rename('energyTemp')
        energy_next.rename('energy')
        energy.rename('energyNext')
        energy = snapshot.collection('energy')
        energy_next = snapshot.collection('energyNext')

    # Compute Aura scores

    snapshot.aql.execute('''
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
                
    ''', bind_vars={
        "flaggingMultiplier": FLAGGING_MULTIPLIER,
        "ratingCutoffHours": RATING_CUTOFF_HOURS,
        "allowedRatings": ALLOWED_RATINGS_PER_CUTOFF,
    })

    # Transfer the aura collection from snapshot to _system

    result = os.system(f'arangodump --overwrite true --compress-output false --server.password "" --server.endpoint "tcp://{config.BN_ARANGO_HOST}:{config.BN_ARANGO_PORT}" --output-directory {AURA_SNAPSHOT_DIR} --server.database snapshot --collection aura')
    assert result == 0, "Aura: dumping aura collection failed."
    result = os.system(f"arangorestore --server.username 'root' --server.password '' --server.endpoint 'tcp://{config.BN_ARANGO_HOST}:{config.BN_ARANGO_PORT}' --input-directory {AURA_SNAPSHOT_DIR} ")
    assert result == 0, "Aura: restoring aura collection failed."

if __name__ == "__main__":
    verify(0)
    print("Aura processing finished")
