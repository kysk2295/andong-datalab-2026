import {Source} from 'three';

// WebGL texture storage is immutable in size. Drop the small placeholder's GPU
// allocation before replacing it with a full-resolution image, including clones.
export function replaceTextureImage(texture,clients,image) {
  const clones=[...clients],textures=[texture,...clones],source=new Source(image);
  for(const current of textures)current.dispose();
  for(const current of textures){current.source=source;current.needsUpdate=true;}
  for(const clone of clones)clients.add(clone);
}
