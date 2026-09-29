import * as THREE from 'three';

// A closed bed under the ballast. Elevated tracks use a concrete beam; ground
// tracks have an embankment reaching the local terrain at both sides.
export function railwayBed(track, groundAt) {
  const positions=[],triangle=(a,b,c)=>positions.push(...a,...c,...b);
  const quad=(a,b,c,d)=>{triangle(a,b,c);triangle(a,c,d);};
  for(let i=1;i<track.path.length;i++){
    const a=track.path[i-1],b=track.path[i],length=Math.hypot(b.x-a.x,b.z-a.z);
    const nx=-(b.z-a.z)/length,nz=(b.x-a.x)/length,width=track.bridge?.005:.006;
    const corner=(p,side,bottom)=>{
      const x=p.x+nx*width*side,z=p.z+nz*width*side;
      return [x,bottom?(track.bridge?p.height-.006:Math.min(groundAt(x,z)-.001,p.height-.001)):p.height+.0006,z];
    };
    const l=corner(a,-1,false),r=corner(a,1,false),L=corner(b,-1,false),R=corner(b,1,false);
    const lb=corner(a,-1,true),rb=corner(a,1,true),Lb=corner(b,-1,true),Rb=corner(b,1,true);
    quad(l,L,R,r);quad(lb,rb,Rb,Lb);quad(l,lb,Lb,L);quad(r,R,Rb,rb);quad(l,r,rb,lb);quad(L,Lb,Rb,R);
  }
  const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.Float32BufferAttribute(positions,3));geometry.computeVertexNormals();
  return geometry;
}

export function railwayPiers(curve, groundAt, step=.06) {
  const parts=[],length=curve.getLength(),count=Math.max(1,Math.ceil(length/step));
  for(let i=0;i<count;i++){
    const p=curve.getPointAt((i+.5)/count),dir=curve.getTangentAt((i+.5)/count),yaw=Math.atan2(dir.x,dir.z);
    const ground=Math.min(...[-1,1].flatMap(x=>[-1,1].map(z=>groundAt(p.x+Math.cos(yaw)*x*.004+Math.sin(yaw)*z*.0045,p.z-Math.sin(yaw)*x*.004+Math.cos(yaw)*z*.0045)))),top=p.y-.006;
    if(top-ground<.002)continue;
    const height=top-ground+.001;
    const pier=new THREE.BoxGeometry(.0045,height,.005);
    pier.rotateY(yaw);
    pier.translate(p.x,ground-.001+height/2,p.z);parts.push(pier);
    const foot=new THREE.BoxGeometry(.008,.002,.009);foot.rotateY(Math.atan2(dir.x,dir.z));foot.translate(p.x,ground-.0005,p.z);parts.push(foot);
  }
  return parts;
}
