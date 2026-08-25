import {put,list} from "@vercel/blob";
import {Store} from "./types";
const prefix="pinpilot-state/";
const empty:Store={students:[],approvals:[],logs:[]};
export async function loadStore():Promise<Store>{
  if(!process.env.BLOB_READ_WRITE_TOKEN)return empty;
  const {blobs}=await list({prefix});
  if(!blobs.length)return empty;
  blobs.sort((a,b)=>new Date(b.uploadedAt).getTime()-new Date(a.uploadedAt).getTime());
  try{return JSON.parse(await (await fetch(blobs[0].url,{cache:"no-store"})).text()) as Store}catch{return empty}
}
export async function saveStore(store:Store){
  await put(`${prefix}state-${Date.now()}.json`,JSON.stringify(store),{access:"private",contentType:"application/json",addRandomSuffix:false});
}
export function log(store:Store,message:string,ok=true){store.logs.unshift({at:new Date().toISOString(),message,ok});store.logs=store.logs.slice(0,100)}
