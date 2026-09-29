import test from 'node:test';
import assert from 'node:assert/strict';
import {RelayAudio} from '../src/relay-audio.js';

function audioContext(){
 const nodes=[];const param=()=>({value:0,setValueAtTime(v){this.value=v;},setTargetAtTime(v){this.value=v;},exponentialRampToValueAtTime(v){this.value=v;}});
 const node=()=>{const n={gain:param(),frequency:param(),connect(){},disconnect(){},start(){this.started=true;},stop(){this.stopped=true;}};nodes.push(n);return n;};
 class Context{constructor(){this.currentTime=0;this.state='running';this.sampleRate=32;Context.count++;}createGain=node;createBufferSource=node;createBiquadFilter=node;createOscillator=node;createBuffer(c,n){return {getChannelData:()=>new Float32Array(n)};}async close(){this.state='closed';}async resume(){this.state='running';}}
 Context.count=0;return {Context,nodes};
}
test('audio is gesture-lazy, quiet when muted or paused, and reusable without duplicate loops',async()=>{
 const {Context}=audioContext(),a=new RelayAudio({AudioContext:Context,enabled:false});await a.unlock();assert.equal(Context.count,0);
 a.setEnabled(true);await a.unlock();await a.unlock();assert.equal(Context.count,1);
 a.setLocation('market');assert.ok(a.room.gain.value>0);assert.ok(a.master.gain.value>0);
 a.setPaused(true);assert.equal(a.master.gain.value,0);assert.equal(a.audible,false);
 a.setPaused(false);a.setEnabled(false);assert.equal(a.master.gain.value,0);
 a.setEnabled(true);a.setLocation('workshop');assert.equal(a.room.gain.value,0);
 a.dispose();assert.equal(a.ctx.state,'closed');await a.unlock();assert.equal(Context.count,1);
});
test('only ground distance produces steps; jumps and camera teleports do not',async()=>{
 const {Context}=audioContext(),a=new RelayAudio({AudioContext:Context});await a.unlock();let steps=0;a.step=()=>steps++;
 a.walk(5);a.walk(.5,true);a.walk(0);assert.equal(steps,0);
 a.walk(.4);a.walk(.4);assert.equal(steps,1);a.setPaused(true);a.walk(.8);assert.equal(steps,1);a.dispose();
});
test('an unavailable audio device does not interrupt the game',async()=>{
 const a=new RelayAudio({AudioContext:class{constructor(){throw Error('unavailable');}}});await a.unlock();assert.equal(a.enabled,false);a.dispose();
});
test('bus engine obeys mute and pause and stops when leaving the vehicle',async()=>{
 const {Context}=audioContext(),a=new RelayAudio({AudioContext:Context});a.setLocation('transit');a.setRide(.7);assert.equal(Context.count,0);await a.unlock();
 assert.ok(a.motorGain.gain.value>0);a.setEnabled(false);assert.equal(a.master.gain.value,0);a.setEnabled(true);a.setPaused(true);assert.equal(a.master.gain.value,0);
 a.setPaused(false);a.setLocation('bridge');assert.equal(a.motorGain.gain.value,0);a.setRide(1);assert.equal(a.motorGain.gain.value,0);a.dispose();assert.equal(a.motor.stopped,true);
});
