// Execute source in a mock WebGL2/DOM VM to smoke-check bootstrap and PLY parsers.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
const source = fs.readFileSync(path.join(__dirname,'../src/projection_mapping/studio_static/studio.js'),'utf8')
  .replace("  setMode('memory');requestAnimationFrame(frame);", "  globalThis.__test={parsePly,parseTextCloud,generateForest,state};setMode('memory');requestAnimationFrame(frame);");
const elements=new Map();
const modes=['memory','spectrum','human'].map(mode=>({dataset:{mode},classList:{toggle(){}},setAttribute(){},addEventListener(){}}));
const gl=new Proxy({}, {get(t,key){
  if(key==='getShaderParameter'||key==='getProgramParameter')return ()=>true;
  if(key==='getShaderInfoLog'||key==='getProgramInfoLog')return ()=>'';
  if(key==='createShader'||key==='createProgram'||key==='createVertexArray'||key==='createBuffer')return ()=>({});
  if(key==='getUniformLocation')return (_,name)=>name;
  if(typeof key==='string'&&key.toUpperCase()===key)return 1;
  return ()=>{};
}});
function el(id){if(!elements.has(id))elements.set(id, {value:'', textContent:'',innerHTML:'',hidden:false,
  getContext:()=>gl,addEventListener(){},classList:{add(){},remove(){},toggle(){}},
  setPointerCapture(){},requestFullscreen(){return Promise.resolve()},clientWidth:1280,clientHeight:750});
  return elements.get(id);
}
const document={getElementById:el,querySelectorAll:()=>modes,addEventListener(){}};
const window={addEventListener(){},devicePixelRatio:1};
const sandbox={document,window,console,navigator:{},Math,Uint8Array,Float32Array,TextDecoder,TextEncoder,DataView,
  ArrayBuffer,Number,setTimeout,clearTimeout,requestAnimationFrame(){},globalThis:null};
sandbox.globalThis=sandbox;
vm.runInNewContext(source,sandbox,{filename:'studio.js'});
const {parsePly,parseTextCloud,generateForest,state}=sandbox.__test;
assert(state.count>20000,'Forest must have spatial density');
const xyz=parseTextCloud('0 0 0\n1 1 1\n','xyz');
assert.equal(xyz.length,14);
assert.equal(xyz[2],-16);
const ply=`ply\nformat ascii 1.0\nelement vertex 3\nproperty float x\nproperty float y\nproperty float z\nproperty uchar red\nproperty uchar green\nproperty uchar blue\nend_header\n0 0 0 255 0 0\n0 1 0 0 255 0\n0 0 1 0 0 255\n`;
const ascii=parsePly(new TextEncoder().encode(ply).buffer);
assert.equal(ascii.length,21);
assert.equal(ascii[3],1);
const head=new TextEncoder().encode('ply\nformat binary_little_endian 1.0\nelement vertex 1\nproperty float x\nproperty float y\nproperty float z\nend_header\n');
const bytes=new Uint8Array(head.length+12);bytes.set(head);const view=new DataView(bytes.buffer);
view.setFloat32(head.length,2,true);view.setFloat32(head.length+4,3,true);view.setFloat32(head.length+8,4,true);
const binary=parsePly(bytes.buffer);
assert.equal(binary.length,7);
assert.equal(binary[2],-12);
assert.throws(()=>parsePly(new TextEncoder().encode('garbage').buffer),/header/i);
console.log('Studio JS mock-WebGL bootstrap, forest and PLY parsers: PASS');
