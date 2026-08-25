export type Source={id:string;name:string,url:string};
const exts=["jpg","jpeg","png","webp"];
export async function scanPublicFolder(folderUrl:string):Promise<Source[]>{
 const id=folderUrl.match(/\/folders\/([a-zA-Z0-9_-]+)/)?.[1]||folderUrl.match(/[?&]id=([a-zA-Z0-9_-]+)/)?.[1];
 if(!id)throw new Error("Invalid Google Drive folder URL");
 if(process.env.GOOGLE_DRIVE_API_KEY){
   const q=encodeURIComponent(`'${id}' in parents and trashed=false`);
   const u=`https://www.googleapis.com/drive/v3/files?q=${q}&fields=files(id,name,mimeType,webContentLink,thumbnailLink)&pageSize=100&key=${process.env.GOOGLE_DRIVE_API_KEY}`;
   const r=await fetch(u,{cache:"no-store"});if(r.ok){const j=await r.json();return (j.files||[]).filter((f:any)=>exts.includes((f.name.split(".").pop()||"").toLowerCase())).map((f:any)=>({id:f.id,name:f.name,url:`https://drive.google.com/uc?export=download&id=${f.id}`}))}
 }
 const html=await (await fetch(`https://drive.google.com/drive/folders/${id}`,{headers:{"User-Agent":"Mozilla/5.0"},cache:"no-store"})).text();
 const ids=[...html.matchAll(/"([a-zA-Z0-9_-]{20,})"/g)].map(m=>m[1]);
 const uniq=[...new Set(ids)].filter(x=>x!==id);
 return uniq.slice(0,100).map((x,i)=>({id:x,name:`Drive image ${i+1}`,url:`https://drive.google.com/uc?export=download&id=${x}`}));
}
export async function download(url:string){const r=await fetch(url,{redirect:"follow",cache:"no-store"});if(!r.ok)throw new Error(`Drive download failed: ${r.status}`);const b=Buffer.from(await r.arrayBuffer());const type=r.headers.get("content-type")?.split(";")[0]||"image/jpeg";return {b,type}}
