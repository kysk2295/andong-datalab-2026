import {RESTAURANT_PASSAGES} from './relay-passages.js';
// Metres. Both seats share the same reachable table approach and seated eye height.
export const DINING_SEATS = Object.freeze({
 center:{name:'가운데 자리',x:0,z:0},
 window:{name:'창가 자리',x:-3,z:-1.55},
});
export function diningSeat(id){return Object.hasOwn(DINING_SEATS,id)?DINING_SEATS[id]:DINING_SEATS.center;}
export function diningStation(id){const {name,x,z}=diningSeat(id);return {name,position:[x,1.22,z+.96],target:[x,.89,z]};}
export function diningLayout(seat='center'){
 return {passages:[RESTAURANT_PASSAGES.dining],bounds:{x:[-4.4,4.4],z:[-3.5,5.9]},obstacles:[
  ...Object.values(DINING_SEATS).map(({x,z})=>({x,z,w:1.75,d:1.15})),
  {x:3,z:-1.6,w:1.5,d:1.15},{x:3.1,z:2.45,w:2.5,d:.95},
  {x:-2.03,z:4.4,w:1.38,d:.05},{x:2.03,z:4.4,w:1.38,d:.05},
  {x:-3.48,z:4.4,w:2.6,d:.15},{x:3.48,z:4.4,w:2.6,d:.15},
 ],stations:{table:diningStation(seat),counter:{name:'식당 계산대',position:[3,1.62,3.8],target:[3.1,1.15,2.4]},door:{name:'식당 입구',position:[0,1.7,5.1],target:[0,1.5,-1]},exit:{name:'식당 밖 골목',position:[0,1.7,5.65],target:[0,1.65,10]}}};
}
