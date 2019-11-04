'use strict';
const createRouter = require('@arangodb/foxx/router');
const joi = require('joi');
const nacl = require('tweetnacl');

const db = require('./db');
const arango = require('@arangodb').db;
const enc = require('./encoding');

const strToUint8Array = enc.strToUint8Array;
const b64ToUint8Array = enc.b64ToUint8Array;

// all keys in the DB are in the url/directory/db safe b64 format
const safe = enc.b64ToUrlSafeB64;

const router = createRouter();
module.context.use(router);

const TIME_FUDGE = 60 * 60 * 1000; // timestamp can be this far in the future (milliseconds) to accommodate client/server clock differences

// Consider using this in the schemas below if they ever update joi
// publicKey1: joi.string().base64().required(),

// lowest-level schemas
var schemas = {
  score: joi.number().min(0).max(100).default(0),
  timestamp: joi.number().integer().required()
};

// extend lower-level schemas with higher-level schemas
schemas = Object.assign({
  user: joi.object({
    key: joi.string().required().description('url-safe public key of the user'),
    score: schemas.score,
    verifications: joi.array().items(joi.string())
  }),
  group: joi.object({
    id: joi.string().required().description('unique identifier of the group'),
    score: schemas.score,
    verifications: joi.array().items(joi.string()),
    isNew: joi.boolean().default(true),
    knownMembers: joi.array().items(joi.string()).description('url-safe public keys of two or three current' +
      ' members connected to the reference user, or if the group is being founded, the co-founders that have joined'),
    founders: joi.array().items(joi.string()).description('url-safe public keys of the three founders of the group')
  }),
  context: joi.object({
    verification: joi.string().required().description('verification used by the context'),
    verificationUrl: joi.string().required().description('the url to PUT a verification with /:id'),
    isApp: joi.boolean().default(false),
    appLogo: joi.string().description('app logo (base64 encoded image)'),
    appUrl: joi.string().description('the base url for the web app associated with the context'),
  }),
}, schemas);

// extend lower-level schemas with higher-level schemas
schemas = Object.assign({

  connectionsPutBody: joi.object({
    publicKey1: joi.string().required().description('public key of the first user (base64)'),
    publicKey2: joi.string().required().description('public key of the second user (base64)'),
    sig1: joi.string().required()
      .description('message (publicKey1 + publicKey2 + timestamp) signed by the user represented by publicKey1'),
    sig2: joi.string().required()
      .description('message (publicKey1 + publicKey2 + timestamp) signed by the user represented by publicKey2'),
    timestamp: schemas.timestamp.description('milliseconds since epoch when the connection occurred')
  }),

  connectionsDeleteBody: joi.object({
    publicKey1: joi.string().required().description('public key of the user removing the connection (base64)'),
    publicKey2: joi.string().required().description('public key of the second user (base64)'),
    sig1: joi.string().required()
      .description('message (publicKey1 + publicKey2 + timestamp) signed by the user represented by publicKey1'),
    timestamp: schemas.timestamp.description('milliseconds since epoch when the removal was requested')
  }),

  membershipGetResponse: joi.object({
    // wrap the data in a "data" object https://jsonapi.org/format/#document-top-level
    data: joi.array().items(joi.string()).description('url-safe public keys of all members of the group')
  }),

  membershipPutBody: joi.object({
    publicKey: joi.string().required().description('public key of the user joining the group (base64)'),
    group: joi.string().required().description('group id'),
    sig: joi.string().required()
      .description('message (publicKey + group + timestamp) signed by the user represented by publicKey'),
    timestamp: schemas.timestamp.description('milliseconds since epoch when the join was requested')
  }),

  membershipDeleteBody: joi.object({
    publicKey: joi.string().required().description('public key of the user leaving the group (base64)'),
    group: joi.string().required().description('group id'),
    sig: joi.string().required()
      .description('message (publicKey + group + timestamp) signed by the user represented by publicKey'),
    timestamp: schemas.timestamp.description('milliseconds since epoch when the removal was requested')
  }),

  groupsPostBody: joi.object({
    publicKey1: joi.string().required().description('public key of the first founder (base64)'),
    publicKey2: joi.string().required().description('public key of the second founder (base64)'),
    publicKey3: joi.string().required().description('public key of the third founder (base64)'),
    sig1: joi.string().required()
      .description('message (publicKey1 + publicKey2 + publicKey3 + timestamp) signed by the user represented by publicKey1'),
    timestamp: schemas.timestamp.description('milliseconds since epoch when the group creation was requested')
  }),

  groupsPostResponse: joi.object({
    // wrap the data in a "data" object https://jsonapi.org/format/#document-top-level
    data: schemas.group
  }),

  groupsDeleteBody: joi.object({
    publicKey: joi.string().required().description('public key of the user deleting the group (base64)'),
    group: joi.string().required().description('group id'),
    sig: joi.string().required()
      .description('message (publicKey + group + timestamp) signed by the user represented by publicKey'),
    timestamp: schemas.timestamp.description('milliseconds since epoch when the removal was requested')
  }),

  fetchUserInfoPostBody: joi.object({
    publicKey: joi.string().required().description('public key of the user (base64)'),
    sig: joi.string().required()
      .description('message (publicKey + timestamp) signed by the user represented by publicKey'),
    timestamp: schemas.timestamp.description('milliseconds since epoch when the removal was requested')
  }),

  fetchUserInfoPostResponse: joi.object({
    data: joi.object({
      score: schemas.score,
      eligibleGroupsUpdated: joi.boolean()
        .description('boolean indicating whether the `eligibleGroups` array returned is up-to-date. If `true`, ' +
          '`eligibleGroups` will contain all eligible groups. If `false`, `eligibleGroups` will only contain eligible groups in the founding stage.'),
      currentGroups: joi.array().items(schemas.group),
      eligibleGroups: joi.array().items(schemas.group),
      connections: joi.array().items(schemas.user),
      verifications: joi.array().items(joi.string()),
      oldIds: joi.array().items(joi.string())
    })
  }),

  usersPostBody: joi.object({
    publicKey: joi.string().required().description("user's public key")
  }),

  usersPostResponse: joi.object({
    // wrap the data in a "data" object https://jsonapi.org/format/#document-top-level
    data: schemas.user
  }),

  fetchVerificationPostBody: joi.object({
    publicKey: joi.string().required().description('public key of the user (base64)'),
    context: joi.string().required().description('the context of the id (typically an application)'),
    id: joi.string().required().description('an id used by the app consuming the verification'),
    sig: joi.string().required().description('message (context + "," + id + "," + timestamp) signed by the user represented by publicKey'),
    timestamp: schemas.timestamp.required().description('milliseconds since epoch when the verification was requested')
  }),

  fetchVerificationPostResponse: joi.object({
    data: joi.object({
      publicKey: joi.string().description("the node's public key."),
      revocableIds: joi.array().items(joi.string()).description("ids formerly used by this user that can be safely revoked"),
      sig: joi.string().description('verification message ( context + "," + id +  "," + timestamp [ + "," + revocableId ... ] ) signed by the node'),
      timestamp: schemas.timestamp.description('milliseconds since epoch when the verification was signed')
    })
  }),

  ipGetResponse: joi.object({
    data: joi.object({
      ip: joi.string().description("IPv4 address in dot-decimal notation.")
    })
  }),

  userScore: joi.object({
    data: joi.object({
      score: schemas.score
    })
  }),

  userConnections: joi.object({
    data: joi.object({
      users: joi.array().items(joi.string())
    })
  }),

  contextsGetResponse: joi.object({
    data: schemas.context
  }),

  trustedConnectionsPostBody: joi.object({
    publicKey: joi.string().required().description('public key of the user (base64)'),
    connections: joi.string().required().description('comma separated list of at least 3 public keys that belongs to trusted connections of the user'),
    sig: joi.string().required()
      .description('message (publicKey + trustedConnections + timestamp) signed by the user represented by publicKey'),
    timestamp: schemas.timestamp.description('milliseconds since epoch when the trusted connections are set')
  }),

  recoverPostBody: joi.object({
    publicKey: joi.string().required().description('public key of the helper user (base64)'),
    oldPublicKey: joi.string().required().description('old public key that is stolen/lost (base64)'),
    newPublicKey: joi.string().required()
      .description('new public key that should be replaced by old public key (base64)'),
    sig: joi.string().required()
      .description('message (publicKey + oldPublicKey + newPublicKey + timestamp) signed by the user represented by publicKey'),
    timestamp: schemas.timestamp.description('milliseconds since epoch when the recovery request is submitted')
  }),

}, schemas);

const handlers = {

  connectionsPut: function connectionsPutHandler(req, res){
    const publicKey1 = req.body.publicKey1;
    const publicKey2 = req.body.publicKey2;
    const timestamp = req.body.timestamp;
    if (timestamp > Date.now() + TIME_FUDGE) {
      res.throw(400, "timestamp can't be in the future");
    }
    const message = strToUint8Array(publicKey1 + publicKey2 + timestamp);

    //Verify signatures
    try {
      if (! nacl.sign.detached.verify(message, b64ToUint8Array(req.body.sig1), b64ToUint8Array(publicKey1))) {
        res.throw(403, "sig1 wasn't publicKey1 + publicKey2 + timestamp signed by the user represented by publicKey1");
      }
      if (! nacl.sign.detached.verify(message, b64ToUint8Array(req.body.sig2), b64ToUint8Array(publicKey2))) {
        res.throw(403, "sig2 wasn't publicKey1 + publicKey2 + timestamp signed by the user represented by publicKey2");
      }
    } catch (e) {
      res.throw(403, e);
    }

    db.addConnection(safe(publicKey1), safe(publicKey2), timestamp);
  },

  connectionsDelete: function connectionsDeleteHandler(req, res){
    const publicKey1 = req.body.publicKey1;
    const publicKey2 = req.body.publicKey2;
    const timestamp = req.body.timestamp;
    if (timestamp > Date.now() + TIME_FUDGE) {
      res.throw(400, "timestamp can't be in the future");
    }
    const message = strToUint8Array(publicKey1 + publicKey2 + req.body.timestamp);

    //Verify signature
    try {
      if (! nacl.sign.detached.verify(message, b64ToUint8Array(req.body.sig1), b64ToUint8Array(publicKey1))) {
        res.throw(403, "sig1 wasn't publicKey1 + publicKey2 + timestamp signed by the user represented by publicKey1");
      }
    } catch (e) {
      res.throw(403, e);
    }
    db.removeConnection(safe(publicKey1), safe(publicKey2), timestamp);
  },

  membershipGet: function membershipGetHandler(req, res){
    const members = db.groupMembers(req.param('groupId'));
    if (! (members && members.length)) {
      res.throw(404, "Group not found");
    }
    res.send({
      "data": members
    });
  },

  membershipPut: function membershipPutHandler(req, res){
    const publicKey = req.body.publicKey;
    const group = req.body.group;
    const timestamp = req.body.timestamp;

    if (timestamp > Date.now() + TIME_FUDGE) {
      res.throw(400, "timestamp can't be in the future");
    }
    const message = strToUint8Array(publicKey + group + timestamp);

    //Verify signature
    try {
      if (! nacl.sign.detached.verify(message, b64ToUint8Array(req.body.sig), b64ToUint8Array(publicKey))) {
        res.throw(403, "sig wasn't publicKey + group + timestamp signed by the user represented by publicKey");
      }
    } catch (e) {
      res.throw(403, e);
    }

    try {
      db.addMembership(group, safe(publicKey), timestamp);
    } catch (e) {
      res.throw(403, e);
    }
  },

  membershipDelete: function membershipDeleteHandler(req, res){
    const publicKey = req.body.publicKey;
    const group = req.body.group;
    const timestamp = req.body.timestamp;

    if (timestamp > Date.now() + TIME_FUDGE) {
      res.throw(400, "timestamp can't be in the future");
    }
    const message = strToUint8Array(publicKey + group + timestamp);

    //Verify signature
    try {
      if (! nacl.sign.detached.verify(message, b64ToUint8Array(req.body.sig), b64ToUint8Array(publicKey))) {
        res.throw(403, "sig wasn't publicKey + group + timestamp signed by the user represented by publicKey");
      }
    } catch (e) {
      res.throw(403, e);
    }

    try {
      db.deleteMembership(group, safe(publicKey), timestamp);
    } catch (e) {
      res.throw(403, e);
    }
  },

  groupsPost: function groupsPostHandler(req, res){
    const publicKey1 = req.body.publicKey1;
    const publicKey2 = req.body.publicKey2;
    const publicKey3 = req.body.publicKey3;
    const timestamp = req.body.timestamp;

    if (timestamp > Date.now() + TIME_FUDGE) {
      res.throw(400, "timestamp can't be in the future");
    }
    const message = strToUint8Array(publicKey1 + publicKey2 + publicKey3 +
      req.body.timestamp);

    //Verify signature
    try {
      if (! nacl.sign.detached.verify(message, b64ToUint8Array(req.body.sig1), b64ToUint8Array(publicKey1))) {
        res.throw(403, "sig1 wasn't publicKey1 + publicKey2 + publicKey3 + timestamp signed by the user represented by publicKey1");
      }
    } catch (e) {
      res.throw(403, e);
    }

    try {
      const group = db.createGroup(safe(publicKey1), safe(publicKey2), safe(publicKey3), timestamp);

      const newGroup = {
        data: {
          id: group._key,
          score: 0,
          isNew: true
        }
      };
      res.send(newGroup);
    } catch (e) {
      res.throw(403, e);
    }
  },

  groupsDelete: function groupsDeleteHandler(req, res){
    const publicKey = req.body.publicKey;
    const group = req.body.group;
    const timestamp = req.body.timestamp;

    if (timestamp > Date.now() + TIME_FUDGE) {
      res.throw(400, "timestamp can't be in the future");
    }
    const message = strToUint8Array(publicKey + group +
      req.body.timestamp);

    //Verify signature
    try {
      if (! nacl.sign.detached.verify(message, b64ToUint8Array(req.body.sig), b64ToUint8Array(publicKey))) {
        res.throw(403, "sig wasn't publicKey + group + timestamp signed by the user represented by publicKey");
      }
    } catch (e) {
      res.throw(403, e);
    }

    try {
      db.deleteGroup(group, safe(publicKey), timestamp);
    } catch (e) {
      res.throw(403, e);
    }
  },

  fetchUserInfo: function usersHandler(req, res){
    const key = req.body.publicKey;
    const timestamp = req.body.timestamp;
    const sig = req.body.sig;

    if (timestamp > Date.now() + TIME_FUDGE) {
      res.throw(400, "timestamp can't be in the future");
    }
    const message = strToUint8Array(key + timestamp);

    //Verify signature
    try {
      if (! nacl.sign.detached.verify(message, b64ToUint8Array(sig), b64ToUint8Array(key))) {
        res.throw(403, "sig wasn't publicKey + timestamp signed by the user represented by publicKey");
      }
    } catch (e) {
      res.throw(403, e);
    }

    const safeKey = safe(key);
    const connections = db.userConnectionsRaw(safeKey);

    const user = db.loadUser(safeKey);
    if (! user) {
      res.throw(404, "User not found");
    }

    const currentGroups = db.userCurrentGroups(safeKey);

    let eligibleGroups = db.userNewGroups(safeKey, connections);
    let eligibleGroupsUpdated = false;
    const groupCheckInterval =
      ((module.context && module.context.configuration && module.context.configuration.groupCheckInterval) || 0);

    if (! user.eligible_timestamp ||
      Date.now() > user.eligible_timestamp + groupCheckInterval) {

      eligibleGroups = eligibleGroups.concat(
        db.userEligibleGroups(safeKey, connections, currentGroups)
      );
      db.updateEligibleTimestamp(safeKey, Date.now());
      eligibleGroupsUpdated = true;
    }

    const oldIds = user.oldIds ? user.oldIds : [];

    res.send({
      data: {
        score: user.score,
        eligibleGroupsUpdated,
        eligibleGroups,
        currentGroups: db.loadGroups(currentGroups, connections, safeKey),
        connections: db.loadUsers(connections),
        verifications: user.verifications,
        oldIds
      }
    });
  },

  fetchVerification: function fetchVerification(req, res){
    const { publicKey: key, context, sig, id, timestamp: userTimestamp } = req.body;

    const serverTimestamp = Date.now();

    if (userTimestamp > serverTimestamp + TIME_FUDGE) {
      res.throw(400, "timestamp can't be in the future");
    }

    let nodePublicKey, nodePrivateKey;

    if (module.context && module.context.configuration && module.context.configuration.publicKey && module.context.configuration.privateKey) {
      nodePublicKey = module.context.configuration.publicKey;
      nodePrivateKey = module.context.configuration.privateKey;
    } else {
      res.throw(500, 'Server node key pair not configured')
    }

    const message = strToUint8Array(context + ',' + id + ',' + userTimestamp);

    try {
      if (! nacl.sign.detached.verify(message, b64ToUint8Array(sig), b64ToUint8Array(key))) {
        res.throw(403, "sig wasn't context + \",\" + id + \",\" + timestamp signed by the user represented by publicKey");
      }
    } catch (e) {
      res.throw(403, e);
    }

    const { verification, collection } = db.getContext(context);

    const coll = arango._collection(collection);

    if (db.latestTimestampForContext(coll, key) > userTimestamp) {
      res.throw(400, "there was an existing mapped account with a more recent timestamp");
    }

    const safeKey = safe(key);

    // check that the user has this verification

    if (! db.userHasVerification(verification, safeKey)) {
      res.throw(400, "user doesn't have the verification for the context")
    }

    // update the id and timestamp and mark it as current in the db

    db.addId(coll, id, safeKey, serverTimestamp);

    // find old ids for this public key that aren't currently being used by someone else

    const revocableIds = db.revocableIds(coll, id, safeKey);

    // sign and return the verification

    const verificationMessage = context + ',' + id + ',' + serverTimestamp + revocableIds.length ? ',' : '' + revocableIds.join(',');

    const verificationSig = nacl.sign.detached(message, b64ToUint8Array(nodePrivateKey));

    res.send({
      data: {
        revocableIds,
        sig: verificationSig,
        timestamp: serverTimestamp,
        publicKey: nodePublicKey
      }
    });

  },

  usersPost: function usersPostHandler(req, res){
    const key = req.body.publicKey;
    const ret = db.createUser(safe(key));
    res.send({ data: ret });
  },

  ip: function ip(req, res){
    let ip = module.context && module.context.configuration && module.context.configuration.ip;
    if (ip) {
      res.send({
        "data": {
          ip,
        }
      });
    } else {
      res.throw(500, "Ip address unknown");
    }
  },

  userScore: function userScore(req, res){
    const score = db.userScore(req.param('user'));
    if (score == null) {
      res.throw(404, "User not found");
    } else {
      res.send({
        "data": {
          score,
        }
      });
    }
  },

  userConnections: function userConnections(req, res){
    const users = db.userConnections(req.param('user'));
    if (users == null) {
      res.throw(404, "User not found");
    } else {
      res.send({
        "data": {
          users,
        }
      });
    }
  },

  contexts: function contexts(req, res){
    const context = db.getContext(req.param('context'));
    if (context == null) {
      res.throw(404, 'Context not found');
    } else {
      res.send({
        "data": context,
      });
    }
  },

  trustedConnections: function trustedConnections(req, res){
    const publicKey = req.body.publicKey;
    const timestamp = req.body.timestamp;
    const connections = req.body.connections;

    if (timestamp > Date.now() + TIME_FUDGE) {
      res.throw(400, "timestamp can't be in the future");
    }
    const message = strToUint8Array(publicKey + connections + timestamp);

    //Verify signature
    try {
      if (! nacl.sign.detached.verify(message, b64ToUint8Array(req.body.sig), b64ToUint8Array(publicKey))) {
        res.throw(403, "sig wasn't publicKey + trustedConnections + timestamp signed by the user represented by publicKey");
      }
    } catch (e) {
      res.throw(403, e);
    }
    if (!db.setTrustedConnections(connections, safe(publicKey))) {
      res.throw(403, "trusted connections can't be overwritten");
    }
  },

  recover: function recover(req, res){
    const publicKey = req.body.publicKey;
    const timestamp = req.body.timestamp;
    const oldPublicKey = req.body.oldPublicKey;
    const newPublicKey = req.body.newPublicKey;

    if (timestamp > Date.now() + TIME_FUDGE) {
      res.throw(400, "timestamp can't be in the future");
    }
    const message = strToUint8Array(publicKey + oldPublicKey + newPublicKey + timestamp);

    //Verify signature
    try {
      if (! nacl.sign.detached.verify(message, b64ToUint8Array(req.body.sig), b64ToUint8Array(publicKey))) {
        res.throw(403, "sig wasn't publicKey + oldPublicKey + newPublicKey + timestamp signed by the user represented by publicKey");
      }
    } catch (e) {
      res.throw(403, e);
    }
    const result = db.recover(safe(publicKey), safe(oldPublicKey), safe(newPublicKey), timestamp);
    if (result != 'success') {
      res.throw(400, result);
    }
  },
};

router.put('/connections/', handlers.connectionsPut)
  .body(schemas.connectionsPutBody.required())
  .summary('Add a connection')
  .description('Adds a connection.')
  .response(null);

router.delete('/connections/', handlers.connectionsDelete)
  .body(schemas.connectionsDeleteBody.required())
  .summary('Remove a connection')
  .description('Removes a connection.')
  .response(null);

router.get('/membership/:groupId', handlers.membershipGet)
  .pathParam('groupId', joi.string().required())
  .summary('Get group members')
  .description('Gets all members of a group.')
  .response(schemas.membershipGetResponse);

router.put('/membership/', handlers.membershipPut)
  .body(schemas.membershipPutBody.required())
  .summary('Join a group')
  .description('Joins a user to a group. A user must have a connection to more than 50% of members and must not have been previously flagged twice for removal.')
  .response(null);

router.delete('/membership/', handlers.membershipDelete)
  .body(schemas.membershipDeleteBody.required())
  .summary('Leave a group')
  .description('Allows a user to leave a group.')
  .response(null);

router.post('/groups/', handlers.groupsPost)
  .body(schemas.groupsPostBody.required())
  .summary('Create a group')
  .description('Creates a group.')
  .response(schemas.groupsPostResponse);

router.delete('/groups/', handlers.groupsDelete)
  .body(schemas.groupsDeleteBody.required())
  .summary('Remove a group')
  .description('Removes a group with three or fewer members (founders). Any of the founders can remove the group.')
  .response(null);

router.post('/fetchUserInfo/', handlers.fetchUserInfo)
  .body(schemas.fetchUserInfoPostBody.required())
  .summary('Get information about a user')
  .description("Gets a user's score, verifications, lists of current groups, eligible groups, and current connections.")
  .response(schemas.fetchUserInfoPostResponse);

router.post('/users/', handlers.usersPost)
  .body(schemas.usersPostBody.required())
  .summary("Create a user")
  .description("Create a user")
  .response(schemas.usersPostResponse);

router.post('/fetchVerification', handlers.fetchVerification)
  .body(schemas.fetchVerificationPostBody.required())
  .summary("Get a signed verification from a server node")
  .description("Gets a signed verification for a user under a given id and context.")
  .response(schemas.fetchVerificationPostResponse);

router.get('/ip/', handlers.ip)
  .summary("Get this server's IPv4 address")
  .response(schemas.ipGetResponse);

router.get('/userScore/:user', handlers.userScore)
  .pathParam('user', joi.string().required().description("Public key of user (url-safe base 64)"))
  .summary("Get a user's score")
  .response(schemas.userScore);

router.get('/userConnections/:user', handlers.userConnections)
  .pathParam('user', joi.string().required().description("Public key of user (url-safe base 64)"))
  .summary("Get a user's connections")
  .response(schemas.userConnections);

router.get('/contexts/:context', handlers.contexts)
  .pathParam('context', joi.string().required().description("Unique name of the context"))
  .summary("Get information about a context")
  .response(schemas.contextsGetResponse);

router.post('/trustedConnections', handlers.trustedConnections)
  .body(schemas.trustedConnectionsPostBody.required())
  .summary("Set trusted connections for a user")
  .description('Set trusted connections who can help users to recover their accounts')
  .response(null);

router.post('/recover', handlers.recover)
  .body(schemas.recoverPostBody.required())
  .summary("Recover lost/stolen brightid")
  .description('Set a new public key for a brightid by its trusted connections')
  .response(null);

module.exports = {
  schemas,
  handlers
};
