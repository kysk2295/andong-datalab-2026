export const contains = (b, [x,y]) => x>=b[0] && x<=b[2] && y>=b[1] && y<=b[3];
export function regionFor(coordinates, coreBounds, regions) {
  if(contains(coreBounds,coordinates))return 'city';
  return regions.find(r=>contains(r.bbox,coordinates))?.id || null;
}
export function regionBudgets(data, mobile) {
  const scale=mobile?.5:1;
  return {cars:data.id?Math.round((data.cars??100)*scale):(mobile?280:720),people:data.id?Math.round((data.people??220)*scale):(mobile?480:1400),trees:data.id?Math.round(5000*scale):(mobile?7000:18000)};
}
