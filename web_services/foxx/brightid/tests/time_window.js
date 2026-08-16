"use strict";

const operations = require("../operations.js");
const db = require("../db.js");
const errors = require("../errors");
const arango = require("@arangodb").db;

const usersColl = arango._collection("users");
const connectionsColl = arango._collection("connections");
const verificationsColl = arango._collection("verifications");
const variablesColl = arango._collection("variables");
const operationCountersColl = arango._collection("operationCounters");
let hashes;

const chai = require("chai");
const should = chai.should();

describe("time window", function () {
  before(function () {
    usersColl.truncate();
    connectionsColl.truncate();
    verificationsColl.truncate();
    usersColl.insert({ _key: "a" });
    usersColl.insert({ _key: "b" });
    usersColl.insert({ _key: "c" });
    const hashes = JSON.parse(
      variablesColl.document("VERIFICATIONS_HASHES").hashes
    );
    const block = Math.max(...Object.keys(hashes));
    verificationsColl.insert({ name: "BrightID", user: "a", block });
    operationCountersColl.truncate();
  });
  after(function () {
    usersColl.truncate();
    connectionsColl.truncate();
    verificationsColl.truncate();
    operationCountersColl.truncate();
  });
  it("should get error after limit", function () {
    operations.checkLimits({ name: "Add Group", id: "a" }, 100, 2);
    operations.checkLimits({ name: "Remove Group", id: "a" }, 100, 2);
    (() => {
      operations.checkLimits({ name: "Add Membership", id: "a" }, 100, 2);
    }).should.throw(errors.TooManyOperationsError);
  });
  it("unverified users should have shared limit", function () {
    const now = Date.now();
    while (Date.now() - now <= 100);
    operations.checkLimits({ name: "Add Group", id: "b" }, 100, 2);
    operations.checkLimits({ name: "Add Group", id: "c" }, 100, 2);
    (() => {
      operations.checkLimits({ name: "Add Membership", id: "b" }, 100, 2);
    }).should.throw(errors.TooManyOperationsError);
  });
  it("connecting to first verified user should set parent", function () {
    db.connect({ id1: "a", id2: "c", level: "just met", timestamp: 1 });
    usersColl.document("c").parent.should.equal("a");
  });
  it("unverified users with parent should have different limit", function () {
    (() => {
      operations.checkLimits({ name: "Add Membership", id: "b" }, 100, 2);
    }).should.throw(errors.TooManyOperationsError);
    operations.checkLimits({ name: "Add Group", id: "c" }, 100, 2);
    operations.checkLimits({ name: "Add Group", id: "c" }, 100, 2);
    (() => {
      operations.checkLimits({ name: "Add Membership", id: "c" }, 100, 2);
    }).should.throw(errors.TooManyOperationsError);
  });
  it("every app should have different limit", function () {
    // Sponsor ops are rate-limited per app AND per signing user (senderAttrs
    // includes both "app" and "id"), and checkLimits only throws once every
    // sender's own bucket is over its limit - so both "app1" and "user1"
    // need to independently exceed the limit for the third call to throw.
    // With limit=1: call 1 fills app1's bucket (returns early on app1,
    // never touching user1's); call 2 exceeds app1's bucket but fills
    // user1's for the first time (returns early on user1); call 3 exceeds
    // both, so neither sender saves it and it throws.
    operations.checkLimits({ name: "Sponsor", app: "app1", id: "user1" }, 100, 1);
    operations.checkLimits({ name: "Sponsor", app: "app1", id: "user1" }, 100, 1);
    (() => {
      operations.checkLimits({ name: "Sponsor", app: "app1", id: "user1" }, 100, 1);
    }).should.throw(errors.TooManyOperationsError);
  });
});
