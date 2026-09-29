import {LatheGeometry,Vector2} from 'three';

// All heights are proportional to radius. Fixed centimetre offsets made the
// inner floor protrude above the rim when a bowl was reduced to teacup size.
export function bowlGeometry(radius){
 const profile=[[0,0],[.35,0],[.65,.22],[.95,.7],[1,.74],[.94,.75],[.9,.65],[.58,.3],[0,.14]];
 return new LatheGeometry(profile.map(([x,y])=>new Vector2(x*radius,y*radius)),64);
}
