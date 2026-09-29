// World-space ripples for both the coloured overview terrain and polygon water.
// Keeping the same clock and coordinates avoids a phase jump when detail opens.
export function animateMapWater(material, time, { terrain = false } = {}) {
  const compile = material.onBeforeCompile;
  const cacheKey = material.customProgramCacheKey();
  material.onBeforeCompile = function(shader, renderer) {
    compile.call(this, shader, renderer);
    shader.uniforms.mapWaterTime = time;
    shader.vertexShader = shader.vertexShader.replace('#include <common>',
      '#include <common>\nvarying vec2 mapWaterXZ;').replace('#include <project_vertex>',
      '#include <project_vertex>\nmapWaterXZ=(modelMatrix*vec4(transformed,1.)).xz;');
    shader.fragmentShader = shader.fragmentShader.replace('#include <common>', `#include <common>
      varying vec2 mapWaterXZ; uniform float mapWaterTime;
      float riverHash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
      float riverNoise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(riverHash(i),riverHash(i+vec2(1.,0.)),f.x),mix(riverHash(i+vec2(0.,1.)),riverHash(i+1.),f.x),f.y);}
    `).replace('#include <map_fragment>', `#include <map_fragment>
      float waterMask=${terrain ? 'step(diffuseColor.r+.035,diffuseColor.b)*step(diffuseColor.g+.025,diffuseColor.b)' : '1.'};
      vec2 riverQ=mapWaterXZ-vec2(-.8,.6)*mapWaterTime*.008;
      float riverGrain=riverNoise(riverQ*40.);
      float riverPhase=dot(riverQ,vec2(135.,190.))+riverGrain*6.;
      float riverDetail=1.-smoothstep(.5,2.5,fwidth(riverPhase));
      float riverCross=sin(dot(riverQ,vec2(-230.,310.))+riverGrain*8.);
      float riverWave=sin(riverPhase)*.65+riverCross*.35;
      float riverCrest=smoothstep(.55,.95,riverWave)*smoothstep(.3,.7,riverNoise(riverQ*85.+3.));
      float riverBroad=sin(dot(riverQ,vec2(28.,36.))+riverGrain*2.);
      diffuseColor.rgb*=1.+waterMask*(riverBroad*.035+riverWave*.06*riverDetail);
      diffuseColor.rgb+=waterMask*vec3(.035,.045,.055)*riverCrest*riverDetail;
    `).replace('#include <normal_fragment_begin>', `#include <normal_fragment_begin>
      vec3 riverTilt=vec3(-.025*cos(riverPhase),0.,-.018*riverCross);
      normal=normalize(normal+(viewMatrix*vec4(riverTilt,0.)).xyz*waterMask*riverDetail);
    `);
  };
  material.customProgramCacheKey = () => `${cacheKey}-map-water-${terrain ? 'terrain' : 'surface'}-v1`;
  return material;
}

export function advanceMapWater(time, dt, running = true, reduced = false) {
  if (running && !reduced && Number.isFinite(dt) && dt > 0) time.value += dt;
}
