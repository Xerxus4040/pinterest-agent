import crypto from "node:crypto";
import {cookies} from "next/headers";
const secret=()=>process.env.APP_ENCRYPTION_KEY||process.env.ADMIN_PASSWORD||"change-me";
export function makeSession(){const exp=Date.now()+1000*60*60*24*7;const body=String(exp);const sig=crypto.createHmac("sha256",secret()).update(body).digest("hex");return `${body}.${sig}`}
export async function isAuthed(){const c=await cookies();const v=c.get("pinpilot_session")?.value;if(!v)return false;const [body,sig]=v.split(".");if(!body||!sig||Number(body)<Date.now())return false;const expected=crypto.createHmac("sha256",secret()).update(body).digest("hex");return crypto.timingSafeEqual(Buffer.from(sig),Buffer.from(expected))}
export function validPassword(p:string){return !!process.env.ADMIN_PASSWORD && p===process.env.ADMIN_PASSWORD}