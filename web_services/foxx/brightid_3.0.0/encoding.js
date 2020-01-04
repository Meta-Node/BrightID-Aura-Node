"use strict";
const B64 = require('base64-js');
const crypto = require('@arangodb/crypto');

function uInt8ArrayToB64(array) {
  const b = Buffer.from(array);
  return b.toString('base64');
}

function b64ToUint8Array(str) {
  // B64.toByteArray might return a Uint8Array, an Array or an Object depending on the platform.
  // Wrap it in Object.values and new Uint8Array to make sure it's a Uint8Array.
  return new Uint8Array(Object.values(B64.toByteArray(str)));
}

function strToUint8Array(str) {
  return new Uint8Array(Buffer.from(str, 'ascii'));
}

function b64ToUrlSafeB64(s) {
  const alts = {
    '/': '_',
    '+': '-',
    '=': ''
  };
  return s.replace(/[/+=]/g, (c) => alts[c]);
}

function urlSafeB64Tob64(s) {
  const alts = {
    '_': '/',
    '-': '+'
  };
  s = s.replace(/[/+=]/g, (c) => alts[c]);
  if (s.length%4 == 2) {
    return s + '==';
  } else if (s.length%4 == 3) {
    return s + '=';
  } else {
    return s;
  }
}

function hash(data) {
  const h = crypto.sha256(data);
  const b = Buffer.from(h, 'hex').toString('base64');
  return b64ToUrlSafeB64(b);
}

module.exports = {
  uInt8ArrayToB64,
  b64ToUint8Array,
  strToUint8Array,
  b64ToUrlSafeB64,
  hash
};