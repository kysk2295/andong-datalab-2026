import test from 'node:test';
import assert from 'node:assert/strict';
import {postcardStampAt} from '../src/relay-popup-postcard.js';
test('postcard hit testing only accepts the three printed stamp regions',()=>{
 assert.equal(postcardStampAt(.23,.48),'moon');assert.equal(postcardStampAt(.5,.48),'bridge');assert.equal(postcardStampAt(.77,.48),'mask');
 for(const [x,y] of [[.5,0],[.5,1],[0,.48],[1,.48],[NaN,.48],[.23,Infinity]])assert.equal(postcardStampAt(x,y),null);
});
