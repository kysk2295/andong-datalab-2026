// Keep the surrounding city visible while replacing just the active detail tile.
// Fragment clipping works for the merged buildings and instanced overview trees.
export function overviewCutout(material, state) {
  const original=material.onBeforeCompile;
  const key=material.customProgramCacheKey();
  material.onBeforeCompile=shader=>{
    original.call(material,shader);
    shader.uniforms.detailBounds=state.bounds;shader.uniforms.detailEnabled=state.enabled;
    shader.vertexShader=shader.vertexShader.replace('#include <common>','#include <common>\nvarying vec2 overviewXZ;').replace('#include <project_vertex>',`#include <project_vertex>
      vec4 overviewPoint=vec4(transformed,1.);
      #ifdef USE_INSTANCING
        overviewPoint=instanceMatrix*overviewPoint;
      #endif
      overviewXZ=(modelMatrix*overviewPoint).xz;
    `);
    shader.fragmentShader=shader.fragmentShader.replace('#include <common>','#include <common>\nvarying vec2 overviewXZ; uniform vec4 detailBounds; uniform float detailEnabled;').replace('#include <clipping_planes_fragment>',`#include <clipping_planes_fragment>
      if(detailEnabled>.5 && overviewXZ.x>detailBounds.x && overviewXZ.y>detailBounds.y && overviewXZ.x<detailBounds.z && overviewXZ.y<detailBounds.w) discard;
    `);
  };
  material.customProgramCacheKey=()=>key+'-detail-cutout-v1';
}
