import * as T from 'three';
import {Reflector} from 'three/addons/objects/Reflector.js';

const FLOW=new T.Vector2(1,.18).normalize(),SPEED=.48;
// Metre-scale swells share their height field with floating boats. Small capillary
// ripples are shaded separately so the river does not need millions of vertices.
const WAVES=[
 {x:.48,z:.17,a:.037,rate:.53,phase:0},
 {x:-.22,z:.68,a:.021,rate:-.37,phase:1.7},
 {x:1.14,z:.81,a:.009,rate:.81,phase:3.4},
];
const gl=n=>Number(n).toFixed(6);
const phase=w=>`(dot(q,vec2(${gl(w.x)},${gl(w.z)}))-(${gl(w.rate)})*uTime+${gl(w.phase)})`;
const waveGLSL=`
 uniform float uTime;uniform vec2 uFlow;uniform float uSpeed;
 float riverHeight(vec2 p){vec2 q=p-uFlow*uSpeed*uTime;return ${WAVES.map(w=>`${gl(w.a)}*sin(${phase(w)})`).join('+')};}
 vec2 riverSlope(vec2 p){vec2 q=p-uFlow*uSpeed*uTime;return ${WAVES.map(w=>`vec2(${gl(w.x*w.a)},${gl(w.z*w.a)})*cos(${phase(w)})`).join('+')};}
`;

export function riverSurfaceAt(x,z,time){
 const qx=x-FLOW.x*SPEED*time,qz=z-FLOW.y*SPEED*time;
 let height=0,slopeX=0,slopeZ=0;
 for(const w of WAVES){const phase=qx*w.x+qz*w.z-w.rate*time+w.phase;height+=w.a*Math.sin(phase);slopeX+=w.a*w.x*Math.cos(phase);slopeZ+=w.a*w.z*Math.cos(phase);}
 return {height,slopeX,slopeZ};
}

export function advanceRiverWater(water,dt,reduced=false){
 // Freeze in place rather than snapping the river back to time zero. Each cached
 // river owns its clock, and hidden pages/paused scenes never advance it.
 if(!water||reduced||!Number.isFinite(dt)||dt<=0)return;
 water.material.uniforms.uTime.value+=dt;
}

export function createRiverWater(width=240,length=310,position=[0,-.3,-20]){
 const shader={
  name:'FlowingRiver',
  uniforms:{color:{value:new T.Color('#10282d')},tDiffuse:{value:null},textureMatrix:{value:new T.Matrix4()},uTime:{value:0},uFlow:{value:FLOW.clone()},uSpeed:{value:SPEED}},
  vertexShader:`${waveGLSL}
   uniform mat4 textureMatrix;varying vec4 mirrorUv;varying vec3 worldPosition;
   void main(){
    vec3 displaced=position;vec3 world=(modelMatrix*vec4(position,1.)).xyz;
    displaced.z+=riverHeight(world.xz);
    worldPosition=(modelMatrix*vec4(displaced,1.)).xyz;
    mirrorUv=textureMatrix*vec4(displaced,1.);
    gl_Position=projectionMatrix*modelViewMatrix*vec4(displaced,1.);
   }`,
  fragmentShader:`${waveGLSL}
   uniform sampler2D tDiffuse;uniform vec3 color;varying vec4 mirrorUv;varying vec3 worldPosition;
   float hash(vec2 p){return fract(sin(dot(p,vec2(127.1,311.7)))*43758.5453);}
   float noise(vec2 p){vec2 i=floor(p),f=fract(p);f=f*f*(3.-2.*f);return mix(mix(hash(i),hash(i+vec2(1.,0.)),f.x),mix(hash(i+vec2(0.,1.)),hash(i+1.),f.x),f.y);}
   void main(){
    vec2 p=worldPosition.xz,q=p-uFlow*uSpeed*uTime;
    float distanceToEye=length(cameraPosition-worldPosition);
    float detail=1.-smoothstep(24.,100.,distanceToEye);
    float swirl=noise(q*.34)*2.-1.;
    vec2 micro=vec2(sin(q.x*3.8+q.y*2.1+swirl*2.4-uTime*.6),cos(q.y*5.2-q.x*2.4+swirl*1.7+uTime*.4));
    vec2 slope=riverSlope(p)+micro*.075*detail;
    vec3 normal=normalize(vec3(-slope.x,1.,-slope.y));
    vec3 eye=normalize(cameraPosition-worldPosition);
    float facing=max(0.,dot(eye,normal));
    float fresnel=.16+.78*pow(1.-facing,3.);
    // Project the normal into screen axes, so ripples remain coherent as the
    // visitor turns their head. Reflection blur softens razor-sharp light bars.
    vec2 distortion=(viewMatrix*vec4(normal-vec3(0.,1.,0.),0.)).xy;
    vec2 uv=mirrorUv.xy/mirrorUv.w+distortion*.045;
    vec2 safeUv=clamp(uv,vec2(.002),vec2(.998));
    vec3 reflection=texture2D(tDiffuse,safeUv).rgb;
    reflection=mix(reflection,(texture2D(tDiffuse,clamp(safeUv+vec2(.0012,.0005),vec2(.002),vec2(.998))).rgb+texture2D(tDiffuse,clamp(safeUv-vec2(.0012,.0005),vec2(.002),vec2(.998))).rgb)*.5,.23);
    vec3 depth=color*.48+vec3(.003,.008,.011)*(swirl*.5+.5);
    vec3 river=mix(depth,reflection*.92,fresnel);
    // Broken surface streaks travel downstream, revealing the current in unlit
    // water. Derivative filtering prevents distant crests from flickering.
    float flowMask=noise(q*vec2(.24,.62)+vec2(0.,swirl));
    float crest=sin(q.x*.9+q.y*4.8+swirl*3.);
    float aa=max(fwidth(crest)*1.2,.055);
    float sheen=smoothstep(.78-aa,.97+aa,crest)*smoothstep(.54,.8,flowMask)*detail;
    river+=vec3(.021,.035,.038)*sheen;
    vec3 halfLight=normalize(eye+normalize(vec3(-.32,.7,-.48)));
    float sparkle=pow(max(dot(normal,halfLight),0.),90.)*.2;
    river+=vec3(.2,.3,.38)*sparkle;
    gl_FragColor=vec4(river,1.);
    #include <tonemapping_fragment>
    #include <colorspace_fragment>
   }`
 };
 // A ~1.5 m grid resolves broad waves; bounded tessellation keeps distant views cheap.
 const geometry=new T.PlaneGeometry(width,length,Math.min(160,Math.max(1,Math.ceil(width/1.5))),Math.min(210,Math.max(1,Math.ceil(length/1.5))));
 geometry.computeBoundingBox();geometry.boundingBox.min.z=-.07;geometry.boundingBox.max.z=.07;geometry.computeBoundingSphere();geometry.boundingSphere.radius+=.07;
 const water=new Reflector(geometry,{color:'#10282d',textureWidth:768,textureHeight:768,clipBias:.002,multisample:0,shader});
 water.name='flowing-river';water.rotation.x=-Math.PI/2;water.position.fromArray(position);water.userData.scenery=true;
 const renderReflection=water.onBeforeRender;
 water.onBeforeRender=function(renderer,scene,camera){if(!scene.overrideMaterial)renderReflection.call(this,renderer,scene,camera);};
 water.userData.dispose=()=>{water.getRenderTarget().dispose();water.geometry.dispose();water.material.dispose();};
 return water;
}
