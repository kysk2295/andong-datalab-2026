import * as THREE from 'three';
import { railwayProfiles } from './railway-profile.js';
import { railwayBed, railwayPiers } from './railway-structure.js';

// Track positions are mapped railways. Train shape, frequency and motion are
// illustrative and deliberately have no live service number or timetable.
export class RailwayScene {
  constructor(d) {
    this.d=d;this.coaches=[];
    const ballast=[],rails=[],sleepers=[],paths=[],decks=[],banks=[],piers=[];
    const groundAt=(x,z)=>d.point(d.a.project.toGeo(x,z)).y;
    this.tracks=railwayProfiles(d.data.railways||[],d.a.project,groundAt);
    let tieCount=0;
    for(const track of this.tracks){
      const c=track.coordinates,surface=track.surface;
      if(c.length<2)continue;
      ballast.push(d.ribbon(c,.008,.001,0,surface));
      for(const offset of [-.0015,.0015])rails.push(d.ribbon(c,.00045,.0018,offset,surface));
      const curve=new THREE.CurvePath();
      for(let i=1;i<track.path.length;i++){
        const a=track.path[i-1],b=track.path[i];
        curve.add(new THREE.LineCurve3(new THREE.Vector3(a.x,a.height,a.z),new THREE.Vector3(b.x,b.height,b.z)));
      }
      (track.bridge?decks:banks).push(railwayBed(track,groundAt));
      if(track.bridge)piers.push(...railwayPiers(curve,groundAt));
      const length=curve.getLength();
      if(length>.24)paths.push({curve,length,surface});
      for(let distance=.005;distance<length&&tieCount<6000;distance+=.007,tieCount++){
        const p=curve.getPointAt(distance/length),dir=curve.getTangentAt(distance/length),g=new THREE.BoxGeometry(.0052,.0007,.0009);
        g.rotateX(-Math.atan2(dir.y,Math.hypot(dir.x,dir.z)));g.rotateY(Math.atan2(dir.x,dir.z));
        g.translate(p.x,p.y+.0013,p.z);sleepers.push(g);
      }
    }
    const merge=(parts,color,options={})=>{if(parts.length)d.merge(parts,new THREE.MeshStandardMaterial({color,roughness:1,...options}));};
    merge(decks,'#b3b1a6',{side:THREE.DoubleSide});merge(banks,'#969280',{side:THREE.DoubleSide});merge(piers,'#aaa99d');
    merge(ballast,'#aaa899');merge(sleepers,'#716b5c');merge(rails,'#ced2cc',{roughness:.5,metalness:.25});
    const center=d.point(d.data.center||[128.675,36.5747]);
    this.path=paths.sort((a,b)=>a.curve.getPointAt(.5).distanceTo(center)-b.curve.getPointAt(.5).distanceTo(center))[0];
    if(!this.path)return;
    const white=new THREE.MeshStandardMaterial({color:'#eff0e6',roughness:.7}),blue=new THREE.MeshStandardMaterial({color:'#316989',roughness:.6}),glass=new THREE.MeshStandardMaterial({color:'#2c4249',roughness:.3}),wheelMaterial=new THREE.MeshStandardMaterial({color:'#353a39',roughness:.7});
    for(let i=0;i<4;i++){
      const coach=new THREE.Group();
      for(const [w,h,l,y,material] of [[.0066,.012,.044,.008,white],[.0068,.002,.043,.004,blue],[.0069,.004,.033,.012,glass],[.005,.002,.033,.016,white]]){
        const part=new THREE.Mesh(new THREE.BoxGeometry(w,h,l),material);part.position.y=y;part.castShadow=true;coach.add(part);
      }
      for(const z of [-.014,.014])for(const x of [-.0029,.0029]){
        const wheel=new THREE.Mesh(new THREE.CylinderGeometry(.0015,.0015,.0007,10),wheelMaterial);
        wheel.name='train-wheel';wheel.rotation.z=Math.PI/2;wheel.position.set(x,.0015,z);coach.add(wheel);
      }
      d.group.add(coach);this.coaches.push(coach);
    }
    this.update(0);
  }
  update(time){
    if(!this.path)return;
    const {curve,length}=this.path,head=(time*.025+.23)%(length+.24);
    this.coaches.forEach((coach,i)=>{
      const distance=head-i*.048;coach.visible=distance>.024&&distance<length-.024;
      if(!coach.visible)return;
      const p=curve.getPointAt(distance/length),dir=curve.getTangentAt(distance/length);
      p.y+=.0018;
      coach.position.copy(p);coach.rotation.set(-Math.atan2(dir.y,Math.hypot(dir.x,dir.z)),Math.atan2(dir.x,dir.z),0,'YXZ');
    });
  }
}
