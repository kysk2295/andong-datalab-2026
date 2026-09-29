// Door zones are inside the walkable bounds. Arrival points sit clear of the
// opposite zone, so releasing a movement key cannot bounce between rooms.
export const RESTAURANT_PASSAGES = {
 market:{action:'restaurant:enter',x:[-1.05,1.05],z:[-21.2,-20.9]},
 dining:{action:'restaurant:exit',x:[-1.8,1.8],z:[5.3,5.9]},
};
export const RESTAURANT_ARRIVALS = {
 market:{position:[0,1.7,-19.9],target:[0,1.65,-10]},
 dining:{position:[0,1.7,3.75],target:[0,1.45,-1]},
};
export function passageAt(position,passages=[]){
 return passages.find(p=>position.x>=p.x[0]&&position.x<=p.x[1]&&position.z>=p.z[0]&&position.z<=p.z[1])?.action||null;
}
export function restaurantStage(state){return state.eaten?2:1;}
