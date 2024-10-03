from arango import ArangoClient
import config
import os

client = ArangoClient(hosts=config.ARANGO_SERVER)
system = client.db('_system')
snapshot = client.db('snapshot')

# Constants related to Aura scores

TEAM_OWNERS = [
    'xqmMHQMnBdakxs3sXXjy7qVqPoXmhhwOt4c_z1tSPwM',
    'AsjAK5gJ68SMYvGfCAuROsMrJQ0_83ZS92xy94LlfIA',
]
STARTING_ENERGY = 1000000
HOPS = 4
FLAGGING_MULTIPLIER = 4


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
        let energyPerOwner = @startingEnergy / length(@teamOwners)
    
        for e in @teamOwners
            insert {
                _key: e,
                energy: energyPerOwner
            } in energy
    ''', bind_vars={
        "teamOwners": TEAM_OWNERS,
        "startingEnergy": STARTING_ENERGY
    })

    # Flow the energy

    for i in range(HOPS):

        snapshot.aql.execute('''
            for e in energy
                let scale = sum (
                    for c in connections
                        filter 'manager' in c.auraEvaluations[*].category 
                        filter c._from == concat('users/', e._key)
                        for eval in c.auraEvaluations
                            filter eval.category == 'manager' and eval.evaluation == 'positive'
                            return eval.confidence
                )
                
                for c in connections
                    filter 'manager' in c.auraEvaluations[*].category
                    filter c._from == concat('users/', e._key)
                    let key = split(c._to,'/',2)[1]
                        for eval in c.auraEvaluations
                            filter eval.category == 'manager' and eval.evaluation == 'positive'
                            upsert { _key: key }
                            insert { _key: key, energy: e.energy * eval.confidence / scale }
                            update { energy: OLD.energy + e.energy * eval.confidence / scale }
                            in energyNext
        ''')

        energy.truncate()
        energy.rename('energyTemp')
        energy_next.rename('energy')
        energy.rename('energyNext')
        energy = snapshot.collection('energy')
        energy_next = snapshot.collection('energyNext')

    # Compute scores, levels and impacts for all roles

    # Managers

    snapshot.aql.execute('''
        for c in connections
            filter "manager" in c.auraEvaluations[*].category
        
            let from = split(c._from,'/',2)[1]
            
            let weight = (
                for e in energy
                    filter e._key == from
                    return e.energy
            )[0]
            
            for eval in c.auraEvaluations
                filter eval.category == "manager"
                collect manager = split(c._to,'/',2)[1] into impacts = {
                    evaluator: from,
                    score: weight,
                    confidence: eval.confidence,
                    impact: eval.confidence * 
                            weight *
                            (eval.evaluation == "positive" ? 1 : -1 * @flaggingMultiplier )
                }
            
            let score = sum(impacts[*].impact)
            
            let level = (
                score >= 5000000 ? 2 :
                score >= 1000 ? 1 :
                score >= 0 ? 0 : -1
            )
                    
            let category = {
                name: "manager",
                score,
                level,
                impacts
            }
            
            let categories = (
                for a in aura
                    filter a._key == manager
                    for d in a.domains
                        filter d.name == "BrightID"
                        limit 1
                        return "manager" in d.categories[*].name ?
                        replace_nth(
                            d.categories,
                            position(d.categories[*].name, "manager", true),
                            category
                        ) : append(d.categories, category)
            )[0]
            
            upsert { _key: manager }
            insert {
                _key: manager,
                domains: [
                    {
                        name: "BrightID",
                        categories: [ category ]
                    }
                ]
            }
            update {
                domains: replace_nth(
                    OLD.domains, 
                    position(OLD.domains[*].name, "BrightID", true),
                    {
                        name: "BrightID",
                        categories
                    }
                )
            } in aura
    ''', bind_vars={
        "flaggingMultiplier": FLAGGING_MULTIPLIER,
    })

    # Trainers

    snapshot.aql.execute('''
        for c in connections
            filter "trainer" in c.auraEvaluations[*].category
            
            let from = split(c._from,'/',2)[1]
            
            let evaluator = (
                for a in aura
                    filter a._key == from
                    for d in a.domains
                        filter d.name == "BrightID"
                        limit 1
                        for cat in d.categories
                            filter cat.name == "manager"
                            limit 1
                            return { score: cat.score , level: cat.level }
            )[0]
        
            for eval in c.auraEvaluations
                filter eval.category == "trainer"
                collect trainer = split(c._to,'/',2)[1] into impacts = {
                    evaluator: from,
                    level: evaluator.level,
                    score: evaluator.score,
                    confidence: eval.confidence,
                    impact: eval.confidence *
                            evaluator.score *
                            (eval.evaluation == "positive" ? 1 : -1 * @flaggingMultiplier)
                }
        
            let score = sum(impacts[*].impact)
            
            let level = (
                score >= 25000000 ? 2 :
                score >= 5000000 ? 1 :
                score >= 0 ? 0 : -1
            )
                    
            let category = {
                name: "trainer",
                score,
                level,
                impacts
            }
            
            let categories = (
                for a in aura
                    filter a._key == trainer
                    for d in a.domains
                        filter d.name == "BrightID"
                        limit 1
                        return "trainer" in d.categories[*].name ?
                        replace_nth(
                            d.categories,
                            position(d.categories[*].name, "trainer", true),
                            category
                        ) : append(d.categories, category)
            )[0]
            
            upsert { _key: trainer }
            insert {
                _key: trainer,
                domains: [
                    {
                        name: "BrightID",
                        categories: [ category ]
                    }
                ]
            }
            update {
                domains: replace_nth(
                    OLD.domains, 
                    position(OLD.domains[*].name, "BrightID", true),
                    {
                        name: "BrightID",
                        categories
                    }
                )
            } in aura
    ''', bind_vars={
        "flaggingMultiplier": FLAGGING_MULTIPLIER,
    })

    # Players

    snapshot.aql.execute('''
        for c in connections
            filter "player" in c.auraEvaluations[*].category
            
            let from = split(c._from,'/',2)[1]
            
            let evaluator = (
                for a in aura
                    filter a._key == from
                    for d in a.domains
                        filter d.name == "BrightID"
                        limit 1
                        for cat in d.categories
                            filter cat.name == "trainer"
                            limit 1
                            return { score: cat.score , level: cat.level }
            )[0]
        
            for eval in c.auraEvaluations
                filter eval.category == "player"
                collect player = split(c._to,'/',2)[1] into impacts = {
                    evaluator: from,
                    level: evaluator.level,
                    score: evaluator.score,
                    confidence: eval.confidence,
                    impact: eval.confidence *
                            evaluator.score *
                            (eval.evaluation == "positive" ? 1 : -1 * @flaggingMultiplier)
                }
        
            let score = sum(impacts[*].impact)
            
            let level = (
                score >= 75000000 and (
                    count(impacts[* filter CURRENT.level >= 2 and CURRENT.confidence >=3]) >= 1 or
                    count(impacts[* filter CURRENT.level >= 2 and CURRENT.confidence >=2]) >= 2
                ) ? 3 :
                score >= 20000000 and
                    count(impacts[* filter CURRENT.level >= 1 and CURRENT.confidence >=2]) >= 1 ? 2 :
                score >= 5000000 ? 1 :
                score >= 0 ? 0 : -1
            )
                    
            let category = {
                name: "player",
                score,
                level,
                impacts
            }
            
            let categories = (
                for a in aura
                    filter a._key == player
                    for d in a.domains
                        filter d.name == "BrightID"
                        limit 1
                        return "player" in d.categories[*].name ?
                        replace_nth(
                            d.categories,
                            position(d.categories[*].name, "player", true),
                            category
                        ) : append(d.categories, category)
            )[0]
            
            upsert { _key: player }
            insert {
                _key: player,
                domains: [
                    {
                        name: "BrightID",
                        categories: [ category ]
                    }
                ]
            }
            update {
                domains: replace_nth(
                    OLD.domains, 
                    position(OLD.domains[*].name, "BrightID", true),
                    {
                        name: "BrightID",
                        categories
                    }
                )
            } in aura
    ''', bind_vars={
        "flaggingMultiplier": FLAGGING_MULTIPLIER,
    })

    # Subjects

    snapshot.aql.execute('''
        for c in connections
            filter "subject" in c.auraEvaluations[*].category
            
            let from = split(c._from,'/',2)[1]
            
            let evaluator = (
                for a in aura
                    filter a._key == from
                    for d in a.domains
                        filter d.name == "BrightID"
                        limit 1
                        for cat in d.categories
                            filter cat.name == "player"
                            limit 1
                            return { score: cat.score , level: cat.level }
            )[0]
        
            for eval in c.auraEvaluations
                filter eval.category == "subject"
                collect subject = split(c._to,'/',2)[1] into impacts = {
                    evaluator: from,
                    level: evaluator.level,
                    score: evaluator.score,
                    confidence: eval.confidence,
                    impact: eval.confidence *
                            evaluator.score *
                            (eval.evaluation == "positive" ? 1 : -1 * @flaggingMultiplier)
                }
        
            let score = sum(impacts[*].impact)
            
            let level = (
                score >= 450000000 and (
                    count(impacts[* filter CURRENT.level >= 3 and CURRENT.confidence >=3]) >= 1 or
                    count(impacts[* filter CURRENT.level >= 3 and CURRENT.confidence >=2]) >= 2
                ) ? 4 :
                score >= 150000000 and (
                    count(impacts[* filter CURRENT.level >= 2 and CURRENT.confidence >=3]) >= 1 or
                    count(impacts[* filter CURRENT.level >= 2 and CURRENT.confidence >=2]) >= 2
                ) ? 3 :
                score >= 50000000 and
                    count(impacts[* filter CURRENT.level >= 1 and CURRENT.confidence >=2]) >= 1 ? 2 :
                score >= 10000000 and 
                    count(impacts[* filter CURRENT.level >= 1 and CURRENT.confidence >=1]) >= 1 ? 1 :
                score >= 0 ? 0 : -1
            )
                    
            let category = {
                name: "subject",
                score,
                level,
                impacts
            }
            
            let categories = (
                for a in aura
                    filter a._key == subject
                    for d in a.domains
                        filter d.name == "BrightID"
                        limit 1
                        return "subject" in d.categories[*].name ?
                        replace_nth(
                            d.categories,
                            position(d.categories[*].name, "subject", true),
                            category
                        ) : append(d.categories, category)
            )[0]
            
            upsert { _key: subject }
            insert {
                _key: subject,
                name: "Aura",
                domains: [
                    {
                        name: "BrightID",
                        categories: [ category ]
                    }
                ]
            }
            update {
                domains: replace_nth(
                    OLD.domains, 
                    position(OLD.domains[*].name, "BrightID", true),
                    {
                        name: "BrightID",
                        categories
                    }
                )
            } in aura
    ''', bind_vars={
        "flaggingMultiplier": FLAGGING_MULTIPLIER,
    })

    # Transfer the aura collection from snapshot to _system

    result = os.system(
        f'arangodump --overwrite true --compress-output false --server.password ""'
        f' --server.endpoint "tcp://{config.BN_ARANGO_HOST}:{config.BN_ARANGO_PORT}"'
        f' --output-directory {config.AURA_SNAPSHOT_DIR} --server.database snapshot'
        f' --collection aura'
    )
    assert result == 0, "Aura: dumping aura collection failed."
    result = os.system(
        f'arangorestore --server.username "root" --server.password "" --server.endpoint'
        f' "tcp://{config.BN_ARANGO_HOST}:{config.BN_ARANGO_PORT}" --input-directory {config.AURA_SNAPSHOT_DIR}'
    )
    assert result == 0, "Aura: restoring aura collection failed."

    # Write the verifications

    system.aql.execute('''
        for a in aura
            insert {
                name: "Aura",
                user: a._key,
                block: @block,
                timestamp: date_now(),
                domains: a.domains
            } into verifications
    ''', bind_vars={
        "block": block,
    })


if __name__ == "__main__":
    verify(0)
    print("Aura processing finished")
