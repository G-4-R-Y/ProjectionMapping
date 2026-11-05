/* Projection Studio: dependency-free WebGL2 preview. Imported media never leaves the browser. */
(() => {
  'use strict';
  const $ = (id) => document.getElementById(id);
  const canvas = $('stage');
  const gl = canvas.getContext('webgl2', { alpha: false, antialias: true, powerPreference: 'high-performance' });
  if (!gl) { $('no-webgl').hidden = false; $('status').textContent = 'WEBGL2 UNAVAILABLE'; return; }

  const vertexSource = `#version 300 es
precision highp float;
layout(location=0) in vec3 a_position;
layout(location=1) in vec3 a_color;
layout(location=2) in float a_seed;
uniform vec2 u_resolution;
uniform float u_time, u_speed, u_twist, u_size, u_light, u_yaw, u_pitch;
uniform int u_kind, u_scene, u_palette;
out vec3 v_color;
out float v_alpha;
mat2 spin(float a) { return mat2(cos(a),sin(a),-sin(a),cos(a)); }
void main() {
  vec3 p = a_position;
  float seed = a_seed;
  if (u_kind == 0) {
    // Travel through a repeating corridor. The GPU moves the points; buffers stay resident.
    p.z = -mod(-p.z - 2.0 - u_time * u_speed * 2.0 + 120.0, 120.0) - 2.0;
  }
  if (u_kind == 0 || u_kind == 1) {
    float bend = u_twist * (u_scene == 1 ? 1.5 : 0.07);
    float phase = u_time * 0.13 + p.z * (u_scene == 1 ? 0.045 : 0.01);
    p.xy = spin(bend * phase) * p.xy;
    if (u_scene == 2) {
      float dissolve = pow(max(sin(u_time * 0.7 + seed * 16.0), 0.0), 3.0);
      p.xy += vec2(sin(seed * 120.0), cos(seed * 97.0)) * dissolve * u_twist * 2.8;
    }
  }
  if (u_kind == 2) { p.x += sin(u_time * 0.25 + p.z * .15) * .15; }
  if (u_kind == 3) { p.xy += vec2(sin(seed * 90.0 + u_time),cos(seed * 70.0 + u_time)) * u_twist * 0.14; }
  p.xz = spin(u_yaw) * p.xz;
  p.yz = spin(u_pitch) * p.yz;
  float distance = max(-p.z, 0.14);
  float perspective = 1.7 / distance;
  vec2 clip = p.xy * perspective;
  clip.x *= u_resolution.y / max(u_resolution.x, 1.0);
  gl_Position = vec4(clip, clamp(1.0 - .12 / distance, 0.0, .999), 1.0);
  gl_PointSize = clamp(u_size * (u_kind == 0 ? 14.0 : 19.0) / max(distance, 1.0), .75, 4.5);
  float fog = 1.0 / (1.0 + distance * (u_kind == 0 ? .022 : .012));
  float luminance = dot(a_color, vec3(.2126,.7152,.0722));
  vec3 c = a_color;
  if (u_palette == 0) c = vec3(luminance);
  if (u_palette == 1) c = mix(vec3(.11,.87,.96), vec3(.94,.20,.78), .5 + .5 * sin(seed * 9.0 + p.x * .3));
  if (u_palette == 2) c = mix(vec3(1.0,.42,.15), vec3(1.0,.82,.45), .5 + .5 * sin(seed * 10.0));
  v_color = c * u_light * (0.62 + .38 * luminance);
  v_alpha = fog * (u_kind == 0 ? .78 : .87);
}`;
  const fragmentSource = `#version 300 es
precision highp float;
in vec3 v_color;
in float v_alpha;
out vec4 fragColor;
void main() {
  vec2 q = gl_PointCoord * 2.0 - 1.0;
  float d = length(q);
  if (d > 1.0) discard;
  float core = 1.0 - smoothstep(.05,.78,d);
  fragColor = vec4(v_color * (0.75 + .25 * core), v_alpha * core);
}`;

  function shader(type, source) {
    const s = gl.createShader(type);
    gl.shaderSource(s, source);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      throw new Error(gl.getShaderInfoLog(s) || 'Shader compilation failed');
    }
    return s;
  }
  let program;
  try {
    program = gl.createProgram();
    gl.attachShader(program, shader(gl.VERTEX_SHADER, vertexSource));
    gl.attachShader(program, shader(gl.FRAGMENT_SHADER, fragmentSource));
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(program));
  } catch (error) { $('no-webgl').hidden = false; $('no-webgl').textContent = `GPU shader unavailable: ${error.message}`; return; }
  gl.useProgram(program);
  const uniforms = Object.fromEntries(['resolution','time','speed','twist','size','light','yaw','pitch','kind','scene','palette'].map(k => [k,gl.getUniformLocation(program, `u_${k}`)]));
  const vao = gl.createVertexArray();
  const buffer = gl.createBuffer();
  gl.bindVertexArray(vao);
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
  gl.enableVertexAttribArray(0); gl.vertexAttribPointer(0,3,gl.FLOAT,false,28,0);
  gl.enableVertexAttribArray(1); gl.vertexAttribPointer(1,3,gl.FLOAT,false,28,12);
  gl.enableVertexAttribArray(2); gl.vertexAttribPointer(2,1,gl.FLOAT,false,28,24);
  gl.bindVertexArray(null);
  gl.enable(gl.BLEND);
  // Deliberately NOT additive: normal alpha compositing preserves a true black floor.
  gl.blendFunc(gl.SRC_ALPHA,gl.ONE_MINUS_SRC_ALPHA);
  gl.disable(gl.DEPTH_TEST);

  const state = { mode:'memory',kind:0,scene:0,palette:0,count:0,points:null,imported:null,time:0,
    speed:.75,twist:.35,size:1.30,light:.85,yaw:0,pitch:0,dragging:false,frames:0,clock:0,
    audio:null,micStream:null,camStream:null,video:$('camera-video'),history:[],humanPrev:null,lastUpdate:0 };
  const labels = {
    memory:['SPATIAL MEMORIES','SPATIAL MEMORY / 001','Between<br>the trees<span>.</span>','A place suspended between geometry and memory.'],
    spectrum:['SPECTRAL REACTOR','AV INSTRUMENT / 002','Sound<br>becomes space<span>.</span>','A sculpted frequency landscape, synchronized to sound.'],
    human:['HUMAN CLOUD','HUMAN FIELD / 003','Bodies<br>of light<span>.</span>','Local camera-reactive points. Pose estimation is not enabled.'],
  };
  let toastTimer;
  function toast(message) { const el=$('toast'); el.textContent=message; el.classList.add('show'); clearTimeout(toastTimer); toastTimer=setTimeout(()=>el.classList.remove('show'),4200); }
  function random(seed=2026) { let s=seed>>>0; return () => { s=(Math.imul(s,1664525)+1013904223)>>>0; return s/4294967296; }; }
  function point(out,x,y,z,r,g,b,seed) { out.push(x,y,z,r,g,b,seed); }
  function generateForest() {
    const rand=random(0xA11CE); const p=[];
    // Sparse ground (vanishing-point lines), woodland trunks, organic canopy, floating dust.
    for (let z=-3;z>-121;z-=.30) {
      for (const x of [-8,-5,-3,-1.55,1.55,3,5,8]) {
        const shade=.42+rand()*.36;
        point(p,x+(rand()-.5)*.05,-2.48,z,shade,shade,shade,rand());
      }
      for(let k=0;k<14;k++) {
        const x=(rand()-.5)*24;
        if(Math.abs(x)<1.45 && rand()<.85) continue;
        const y=-2.5+Math.sin(x*.7+z*.11)*.055;
        const shade=.14+rand()*.5;
        point(p,x,y,z+(rand()-.5)*.2,shade,shade,shade,rand());
      }
    }
    for(let i=0;i<210;i++) {
      const side=i%2?1:-1, x=side*(2.7+rand()*9.5), z=-4-rand()*116;
      const height=2.8+rand()*6, trunkWidth=.05+rand()*.18, lean=(rand()-.5)*.8;
      for(let j=0;j<46;j++) {
        const f=j/46, shade=.26+rand()*.45;
        point(p,x+lean*f+(rand()-.5)*trunkWidth,-2.48+height*f,z+(rand()-.5)*trunkWidth,shade,shade,shade,rand());
      }
      for(let j=0;j<9;j++) {
        const a=rand()*Math.PI*2, f=.4+rand()*.5, length=.7+rand()*3.5;
        for(let k=0;k<28;k++) {
          const t=k/28, shade=.13+rand()*.62;
          point(p,x+lean*f+Math.cos(a)*length*t,-2.48+height*f+length*t*(rand()*.2-.08),z+Math.sin(a)*length*t,shade,shade,shade,rand());
        }
      }
      for(let j=0;j<85;j++) {
        const a=rand()*Math.PI*2, h=(rand()-.5)*2, radius=Math.sqrt(rand())*(1.1+rand()*2.3);
        const shade=.08+rand()*.55;
        point(p,x+lean+Math.cos(a)*radius,-2.48+height+h,z+Math.sin(a)*radius,shade,shade,shade,rand());
      }
    }
    for(let i=0;i<6200;i++) {
      const x=(rand()-.5)*25,y=-2.3+rand()*10,z=-3-rand()*118;
      const shade=.14+Math.pow(rand(),3)*.86;
      point(p,x,y,z,shade,shade,shade,rand());
    }
    return new Float32Array(p);
  }
  function pushPoints(data, kind, source) {
    if(!data.length) throw new Error('No usable points were found.');
    state.points=data;state.count=data.length/7;state.kind=kind;
    gl.bindBuffer(gl.ARRAY_BUFFER,buffer); gl.bufferData(gl.ARRAY_BUFFER,data,gl.DYNAMIC_DRAW);
    $('point-count').textContent=`${state.count.toLocaleString()} POINTS`;
    $('source-label').textContent=source;
  }
  function normalizeCloud(points) {
    const count=points.length/7; if(!count) throw new Error('Empty point cloud.');
    const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
    for(let i=0;i<points.length;i+=7) for(let j=0;j<3;j++) {min[j]=Math.min(min[j],points[i+j]);max[j]=Math.max(max[j],points[i+j]);}
    const center=min.map((v,j)=>(v+max[j])/2),extent=Math.max(...max.map((v,j)=>v-min[j]));
    const scale=8/Math.max(extent,1e-5);
    for(let i=0;i<points.length;i+=7) {
      points[i]=(points[i]-center[0])*scale;points[i+1]=(points[i+1]-center[1])*scale;
      points[i+2]=(points[i+2]-center[2])*scale-12;
    }
    return points;
  }
  const MAX_POINTS=130000,MAX_BYTES=40*1024*1024;
  function cloudRows(rows,ix,iy,iz,ir=-1,ig=-1,ib=-1,count=rows.length) {
    if([ix,iy,iz].some(i=>i<0)) throw new Error('Point cloud needs x, y and z coordinates.');
    const out=[],step=Math.max(1,Math.ceil(count/MAX_POINTS));
    for(let k=0;k<Math.min(count,rows.length);k+=step) {
      const v=rows[k];if(!v)continue;
      const xyz=[Number(v[ix]),Number(v[iy]),Number(v[iz])];if(!xyz.every(Number.isFinite))continue;
      const hasColor=ir>=0&&ig>=0&&ib>=0;
      const raw=hasColor?[Number(v[ir]),Number(v[ig]),Number(v[ib])]:[.86,.89,.91];
      const rgb=raw.every(Number.isFinite)?raw:[.86,.89,.91];
      const denom=Math.max(...rgb)>1?255:1;
      point(out,...xyz,...rgb.map(x=>Number.isFinite(x)?Math.max(0,Math.min(1,x/denom)):.8),k/count);
    }
    return normalizeCloud(new Float32Array(out));
  }
  function parseTextCloud(text,extension) {
    let lines=text.split(/\r?\n/).filter(l=>l.trim() && !l.trim().startsWith('#'));
    if(extension==='pts'&&/^\d+$/.test(lines[0]?.trim()))lines=lines.slice(1);
    const rows=lines.map(l=>l.trim().split(/[\s,]+/));
    return cloudRows(rows,0,1,2,3,4,5);
  }
  const numericTypes={char:[1,'getInt8'],int8:[1,'getInt8'],uchar:[1,'getUint8'],uint8:[1,'getUint8'],short:[2,'getInt16'],int16:[2,'getInt16'],ushort:[2,'getUint16'],uint16:[2,'getUint16'],int:[4,'getInt32'],int32:[4,'getInt32'],uint:[4,'getUint32'],uint32:[4,'getUint32'],float:[4,'getFloat32'],float32:[4,'getFloat32'],double:[8,'getFloat64'],float64:[8,'getFloat64']};
  function parsePly(buffer) {
    const bytes=new Uint8Array(buffer),endMark=new TextEncoder().encode('end_header');
    let marker=-1;for(let i=0;i<Math.min(bytes.length-endMark.length,65536);i++){
      let match=true;for(let j=0;j<endMark.length;j++)if(bytes[i+j]!==endMark[j]){match=false;break;}
      if(match){marker=i+endMark.length;break;}
    }
    if(marker<0)throw new Error('PLY header missing or too large.');
    let body=marker;while(body<bytes.length&&(bytes[body]===10||bytes[body]===13))body++;
    const header=new TextDecoder().decode(bytes.subarray(0,marker));
    if(!header.startsWith('ply'))throw new Error('Invalid PLY file.');
    const fmt=/^format\s+(\S+)\s+1\.0\s*$/m.exec(header)?.[1];
    const count=Number(/^element\s+vertex\s+(\d+)\s*$/m.exec(header)?.[1]);
    if(!Number.isSafeInteger(count)||count<1||count>50000000)throw new Error('Invalid PLY vertex count.');
    const start=header.indexOf('element vertex ');
    if(start<0)throw new Error('PLY file has no vertex element.');
    const tail=header.slice(start).split(/\r?\n/).slice(1);
    const properties=[];
    for(const row of tail){if(!row.startsWith('property '))break;const parts=row.trim().split(/\s+/);if(parts[1]==='list')throw new Error('PLY list vertices are unsupported.');properties.push({type:parts[1],name:parts[2]});}
    const ix=properties.findIndex(x=>x.name==='x'),iy=properties.findIndex(x=>x.name==='y'),iz=properties.findIndex(x=>x.name==='z');
    const ir=properties.findIndex(x=>x.name==='red'),ig=properties.findIndex(x=>x.name==='green'),ib=properties.findIndex(x=>x.name==='blue');
    if([ix,iy,iz].some(i=>i<0))throw new Error('PLY needs x/y/z vertex properties.');
    if(fmt==='ascii'){
      const rows=new TextDecoder().decode(bytes.subarray(body)).split(/\r?\n/).slice(0,count).map(l=>l.trim().split(/\s+/));
      return cloudRows(rows,ix,iy,iz,ir,ig,ib,count);
    }
    if(fmt!=='binary_little_endian')throw new Error('Only ASCII and binary little-endian PLY are supported.');
    let stride=0;for(const p of properties){if(!numericTypes[p.type])throw new Error(`Unsupported PLY type: ${p.type}`);stride+=numericTypes[p.type][0];}
    if(body+count*stride>bytes.length)throw new Error('PLY vertex data is truncated.');
    const view=new DataView(buffer),out=[],step=Math.max(1,Math.ceil(count/MAX_POINTS));
    for(let i=0;i<count;i+=step){const row=[];let offset=body+i*stride;
      for(const p of properties){const [length,getter]=numericTypes[p.type];row.push(view[getter](offset,true));offset+=length;}
      const xyz=[row[ix],row[iy],row[iz]];if(!xyz.every(Number.isFinite))continue;
      const hasColor=ir>=0&&ig>=0&&ib>=0;
      const rgb=hasColor?[row[ir]/255,row[ig]/255,row[ib]/255]:[.86,.89,.91];
      point(out,...xyz,...rgb.map(v=>Math.max(0,Math.min(1,v))),i/count);
    }
    return normalizeCloud(new Float32Array(out));
  }
  async function imageRelief(file) {
    const bitmap=await createImageBitmap(file);
    try {
      if(bitmap.width*bitmap.height>40000000)throw new Error('Image exceeds the 40-megapixel local limit.');
      const w=Math.max(2,Math.min(240,bitmap.width)),h=Math.max(2,Math.round(w*bitmap.height/bitmap.width));
      const tmp=document.createElement('canvas');tmp.width=w;tmp.height=h;const ctx=tmp.getContext('2d',{willReadFrequently:true});
      ctx.drawImage(bitmap,0,0,w,h);const pixels=ctx.getImageData(0,0,w,h).data,out=[];
      for(let y=0;y<h;y++)for(let x=0;x<w;x++){
        const i=(y*w+x)*4;if(pixels[i+3]<32)continue;
        const r=pixels[i]/255,g=pixels[i+1]/255,b=pixels[i+2]/255,lum=.2126*r+.7152*g+.0722*b;
        if(lum<.025 && ((x+y)%3!==0))continue;
        const xx=(x/(w-1)-.5)*12,yy=(.5-y/(h-1))*12*h/w;
        const zz=-10.5+(lum-.5)*3.3;
        point(out,xx,yy,zz,r,g,b,(x+y*w)/(w*h));
      }
      return new Float32Array(out);
    } finally { bitmap.close(); }
  }
  async function loadFile(file) {
    if(!file)return;
    if(file.size>MAX_BYTES)throw new Error('Use files smaller than 40 MB in this preview. Larger scans need streaming/LOD.');
    let data,source;
    if(file.type.startsWith('image/')||/\.(png|jpe?g|webp)$/i.test(file.name)){
      data=await imageRelief(file);source='2.5D IMAGE RELIEF';
    }else if(/\.ply$/i.test(file.name)){
      data=parsePly(await file.arrayBuffer());source='PLY FILE';
    }else if(/\.(xyz|pts)$/i.test(file.name)){
      data=parseTextCloud(await file.text(),file.name.split('.').pop().toLowerCase());source='XYZ / PTS FILE';
    }else throw new Error('Use .ply, .xyz, .pts or PNG/JPEG/WebP.');
    if(data.length/7>MAX_POINTS){ // cap image grids as well
      const step=Math.ceil(data.length/7/MAX_POINTS),sampled=[];
      for(let i=0;i<data.length;i+=7*step)sampled.push(...data.subarray(i,i+7));
      data=new Float32Array(sampled);
    }
    state.imported=data;setMode('memory');pushPoints(data,1,source);
    $('scene-title').innerHTML='Your<br>memory<span>.</span>';
    $('scene-subtitle').textContent='Locally rendered. Drag to explore; deform with the controls.';
    toast(`Loaded ${file.name} · ${state.count.toLocaleString()} points · nothing uploaded`);
  }
  async function pasteImage() {
    if(!navigator.clipboard?.read) {toast('Press Ctrl+V to paste an image. Clipboard read requires localhost or HTTPS.');return;}
    try {
      const items=await navigator.clipboard.read();
      for(const item of items)for(const type of item.types)if(type.startsWith('image/')){
        const blob=await item.getType(type);await loadFile(new File([blob],'clipboard.png',{type}));return;
      }
      throw new Error('No image found in clipboard.');
    } catch(error) { toast(`Clipboard: ${error.message}. You can also use Ctrl+V.`); }
  }
  function seedSpectrum() {
    state.history=[];for(let i=0;i<64;i++)state.history.push(new Float32Array(96));
  }
  function spectrumFrame() {
    const bands=new Float32Array(96);
    if(state.audio?.analyser){state.audio.analyser.getByteFrequencyData(state.audio.bytes);
      for(let i=0;i<96;i++){const k=Math.min(state.audio.bytes.length-1,Math.floor(Math.pow(i/95,1.7)*(state.audio.bytes.length-1)));bands[i]=Math.pow(state.audio.bytes[k]/255,1.3);}
    } else {
      for(let i=0;i<96;i++){const u=i/96;
        bands[i]=.07+.16*Math.pow(Math.sin(u*26-state.time*2.5),2)+.23*Math.exp(-Math.pow((u-.19-Math.sin(state.time*.3)*.025)/.06, 2))*(.5+.5*Math.sin(state.time*5));
      }
    }
    state.history.pop();state.history.unshift(bands);
    const data=[];
    for(let j=0;j<state.history.length;j++)for(let i=0;i<96;i++){
      const h=state.history[j][i],x=(i/95-.5)*17,z=-3-j*.42;
      const y=-2+Math.pow(h,.75)*9,seed=i/96;
      point(data,x,y,z,.3+.68*h,.7+.3*h,.87,seed);
      if(i%3===0){point(data,x,-2,z,.18,.28,.38,seed);}
    }
    pushPoints(new Float32Array(data),2,state.audio?'LIVE AUDIO':'DEMO SIGNAL');
  }
  function humanFrame() {
    const video=state.video;if(video.readyState<2)return;
    const c=humanFrame.canvas||(humanFrame.canvas=document.createElement('canvas'));c.width=140;c.height=82;
    const ctx=c.getContext('2d',{willReadFrequently:true});ctx.drawImage(video,0,0,c.width,c.height);
    const rgb=ctx.getImageData(0,0,c.width,c.height).data,lum=new Float32Array(c.width*c.height),data=[];
    for(let i=0;i<lum.length;i++)lum[i]=(.2126*rgb[i*4]+.7152*rgb[i*4+1]+.0722*rgb[i*4+2])/255;
    for(let y=1;y<c.height-1;y++)for(let x=1;x<c.width-1;x++){
      const i=y*c.width+x,grad=Math.abs(lum[i-1]-lum[i+1])+Math.abs(lum[i-c.width]-lum[i+c.width]);
      const movement=state.humanPrev?Math.abs(lum[i]-state.humanPrev[i]):0;
      if(grad<.14 && movement<.095)continue;
      const intensity=Math.min(1,grad*1.8+movement*2.2);
      point(data,(.5-x/(c.width-1))*13,(.5-y/(c.height-1))*8,-8.5-lum[i]*2,intensity,intensity,intensity,i/lum.length);
    }
    state.humanPrev=lum;
    if(data.length)pushPoints(new Float32Array(data),3,'LOCAL CAMERA / EDGES');
  }
  async function toggleMic() {
    if(state.micStream){state.micStream.getTracks().forEach(t=>t.stop());state.micStream=null;
      await state.audio?.ctx.close();state.audio=null;$('mic').textContent='⌁ ENABLE MICROPHONE';toast('Microphone stopped.');return;}
    try {
      if(!navigator.mediaDevices?.getUserMedia)throw new Error('Camera/mic APIs need localhost or HTTPS.');
      const stream=await navigator.mediaDevices.getUserMedia({audio:true,video:false});
      const ctx=new (window.AudioContext||window.webkitAudioContext)();await ctx.resume();
      const analyser=ctx.createAnalyser();analyser.fftSize=1024;analyser.smoothingTimeConstant=.78;
      ctx.createMediaStreamSource(stream).connect(analyser);
      state.micStream=stream;state.audio={ctx,analyser,bytes:new Uint8Array(analyser.frequencyBinCount)};
      setMode('spectrum');$('mic').textContent='■ STOP MICROPHONE';toast('Local microphone spectrum active. Audio is not uploaded or recorded.');
    }catch(error){toast(`Microphone unavailable: ${error.message}`);}
  }
  async function toggleCamera() {
    if(state.camStream){state.camStream.getTracks().forEach(t=>t.stop());state.camStream=null;state.video.srcObject=null;
      $('camera').textContent='◉ ENABLE CAMERA';toast('Camera stopped.');return;}
    try {
      if(!navigator.mediaDevices?.getUserMedia)throw new Error('Camera APIs need localhost or HTTPS.');
      const stream=await navigator.mediaDevices.getUserMedia({video:{facingMode:'user',width:{ideal:640},height:{ideal:480}},audio:false});
      state.camStream=stream;state.video.srcObject=stream;await state.video.play();state.humanPrev=null;
      $('camera').textContent='■ STOP CAMERA';setMode('human');toast('Local camera-reactive preview active. No model inference or uploads.');
    }catch(error){toast(`Camera unavailable: ${error.message}`);}
  }
  function setMode(mode) {
    if(mode!=='memory' && mode!=='spectrum' && mode!=='human')return;
    // Privacy: leaving a media mode releases its device immediately.
    if(mode!=='human' && state.camStream){
      state.camStream.getTracks().forEach(t=>t.stop());state.camStream=null;
      state.video.srcObject=null;state.humanPrev=null;$('camera').textContent='◉ ENABLE CAMERA';
    }
    if(mode!=='spectrum' && state.micStream){
      state.micStream.getTracks().forEach(t=>t.stop());state.micStream=null;
      state.audio?.ctx.close();state.audio=null;$('mic').textContent='⌁ ENABLE MICROPHONE';
    }
    state.mode=mode;
    document.querySelectorAll('.mode').forEach(btn=>{const active=btn.dataset.mode===mode;btn.classList.toggle('active',active);btn.setAttribute('aria-pressed',String(active));});
    const copy=labels[mode];$('breadcrumb').textContent=copy[0];$('eyebrow').textContent=copy[1];$('scene-title').innerHTML=copy[2];$('scene-subtitle').textContent=copy[3];
    if(mode==='memory'){
      if(state.imported)pushPoints(state.imported,1,'IMPORTED POINT CLOUD');
      else pushPoints(generateForest(),0,'PROCEDURAL');
    }else if(mode==='spectrum'){seedSpectrum();spectrumFrame();}
    else if(state.camStream){humanFrame();}else{pushPoints(new Float32Array([0,0,-9,1,1,1,0]),3,'AWAITING CAMERA');toast('Enable camera to generate a local motion/edge point cloud.');}
  }
  function resize() {
    const dpr=Math.min(window.devicePixelRatio||1,1.6);
    const w=Math.max(1,Math.floor(canvas.clientWidth*dpr)),h=Math.max(1,Math.floor(canvas.clientHeight*dpr));
    if(canvas.width!==w||canvas.height!==h){canvas.width=w;canvas.height=h;gl.viewport(0,0,w,h);}
  }
  let previous=0;
  function frame(now) {
    const dt=Math.min((now-previous)/1000||0,.05);previous=now;state.time+=dt;
    resize();
    if(now-state.lastUpdate>75){if(state.mode==='spectrum')spectrumFrame();if(state.mode==='human'&&state.camStream)humanFrame();state.lastUpdate=now;}
    gl.clearColor(0,0,0,1);gl.clear(gl.COLOR_BUFFER_BIT);
    gl.useProgram(program);gl.bindVertexArray(vao);
    gl.uniform2f(uniforms.resolution,canvas.width,canvas.height);
    for(const k of ['time','speed','twist','size','light','yaw','pitch'])gl.uniform1f(uniforms[k],state[k]);
    gl.uniform1i(uniforms.kind,state.kind);gl.uniform1i(uniforms.scene,state.scene);gl.uniform1i(uniforms.palette,state.palette);
    gl.drawArrays(gl.POINTS,0,state.count);
    state.frames++;
    if(now-state.clock>1000){$('frame-rate').textContent=`${Math.round(state.frames*1000/(now-state.clock||1000))} FPS`;state.clock=now;state.frames=0;}
    requestAnimationFrame(frame);
  }
  for(const btn of document.querySelectorAll('.mode'))btn.addEventListener('click',()=>setMode(btn.dataset.mode));
  for(const id of ['speed','twist','size','light'])$(id).addEventListener('input',e=>{
    state[id]=Number(e.target.value);$(`${id}-value`).textContent=state[id].toFixed(2);
  });
  $('scene').addEventListener('change',e=>{state.scene={forest:0,vortex:1,dissolve:2}[e.target.value];});
  $('palette').addEventListener('change',e=>{state.palette={mono:0,cyber:1,ember:2}[e.target.value];});
  $('file-picker').addEventListener('change',async e=>{try{await loadFile(e.target.files[0]);}catch(error){toast(error.message);}e.target.value='';});
  $('paste').addEventListener('click',pasteImage);
  window.addEventListener('paste',async e=>{
    const img=[...e.clipboardData?.items||[]].find(item=>item.type.startsWith('image/'));
    if(img){e.preventDefault();try{await loadFile(new File([img.getAsFile()],'clipboard.png',{type:img.type}));}catch(error){toast(error.message);}}
  });
  $('mic').addEventListener('click',toggleMic);$('camera').addEventListener('click',toggleCamera);
  $('reset').addEventListener('click',()=>{state.yaw=0;state.pitch=0;state.time=0;if(state.mode==='memory'&&!state.imported)setMode('memory');toast('Camera and animation reset.');});
  const fullscreen=()=>{if(document.fullscreenElement)document.exitFullscreen();else $('viewport').requestFullscreen?.().catch(e=>toast(e.message));};
  $('fullscreen').addEventListener('click',fullscreen);
  document.addEventListener('keydown',e=>{
    if(['INPUT','SELECT','TEXTAREA'].includes(document.activeElement?.tagName))return;
    if(['1','2','3'].includes(e.key))setMode({1:'memory',2:'spectrum',3:'human'}[e.key]);
    if(e.key==='F11'){e.preventDefault();fullscreen();}
  });
  canvas.addEventListener('pointerdown',e=>{state.dragging=true;canvas.setPointerCapture(e.pointerId);});
  canvas.addEventListener('pointerup',()=>{state.dragging=false;});
  canvas.addEventListener('pointercancel',()=>{state.dragging=false;});
  canvas.addEventListener('pointermove',e=>{if(!state.dragging)return;state.yaw=Math.max(-.85,Math.min(.85,state.yaw+e.movementX*.0025));state.pitch=Math.max(-.5,Math.min(.5,state.pitch+e.movementY*.0025));});
  canvas.addEventListener('wheel',e=>{e.preventDefault();state.size=Math.max(.5,Math.min(3.5,state.size-e.deltaY*.001));$('size').value=state.size;$('size-value').textContent=state.size.toFixed(2);},{passive:false});
  let depth=0;
  document.addEventListener('dragenter',e=>{if(!e.dataTransfer?.types.includes('Files'))return;e.preventDefault();depth++;$('drop-target').hidden=false;});
  document.addEventListener('dragover',e=>{if(e.dataTransfer?.types.includes('Files'))e.preventDefault();});
  document.addEventListener('dragleave',e=>{e.preventDefault();if(--depth<=0){depth=0;$('drop-target').hidden=true;}});
  document.addEventListener('drop',async e=>{e.preventDefault();depth=0;$('drop-target').hidden=true;try{await loadFile(e.dataTransfer.files[0]);}catch(error){toast(error.message);}});
  window.addEventListener('beforeunload',()=>{state.micStream?.getTracks().forEach(t=>t.stop());state.camStream?.getTracks().forEach(t=>t.stop());});
  canvas.addEventListener('webglcontextlost',e=>{e.preventDefault();$('status').textContent='GPU CONTEXT LOST — RELOAD';});
  setMode('memory');requestAnimationFrame(frame);
})();
