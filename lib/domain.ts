export type Product = { id: string; name: string; unit: string; price: number; capacity: number; emoji: string };
export const products: Product[] = [
 {id:'chocolate',name:'Chocolate Truffle',unit:'1 kg cake',price:900,capacity:4,emoji:'🍫'},
 {id:'vanilla',name:'Vanilla Cloud',unit:'1 kg cake',price:750,capacity:3,emoji:'🍰'},
 {id:'cupcakes',name:'Cupcake Box',unit:'box of 6',price:420,capacity:8,emoji:'🧁'},
 {id:'redvelvet',name:'Red Velvet',unit:'1 kg cake',price:1100,capacity:0,emoji:'♥'}
];
export type Proposal = {intent:'order'|'question'|'handoff'; productId:string|null; quantity:number|null; date:string|null; language:'en'|'hi'; note:string; missing:string[]};
export type Order = {id:string;messageId:string;customer:string;productId:string;quantity:number;date:string;total:number;paid:number;status:'reserved'|'ready'|'completed'|'cancelled'};
export function available(product:Product,date:string,orders:Order[]){return Math.max(0,product.capacity-orders.filter(o=>o.productId===product.id&&o.date===date&&o.status!=='cancelled').reduce((n,o)=>n+o.quantity,0));}
export function alternativesFor(p:Proposal,catalog:Product[],orders:Order[]){
 const requested=catalog.find(x=>x.id===p.productId);const quantity=p.quantity??1;
 if(!requested||!p.date||!validDate(p.date)||!Number.isInteger(quantity)||quantity<1||quantity>50||p.intent==='handoff'||available(requested,p.date,orders)>=quantity)return [];
 return catalog.filter(x=>x.id!==requested.id&&x.unit===requested.unit&&available(x,p.date!,orders)>=quantity);
}
function validDate(value:string){const d=new Date(value+'T12:00:00Z');return Number.isFinite(d.getTime())&&d.toISOString().slice(0,10)===value;}
export function inspect(p:Proposal, catalog:Product[],orders:Order[]){
 const product=catalog.find(x=>x.id===p.productId); const errors:string[]=[];
 if(!product)errors.push('Choose a catalog item');
 if(!Number.isInteger(p.quantity)||!p.quantity||p.quantity<1||p.quantity>50)errors.push('Confirm quantity (1–50)');
 if(!p.date||!/^\d{4}-\d{2}-\d{2}$/.test(p.date)||!validDate(p.date))errors.push('Confirm a valid pickup date');
 if(product&&p.date&&p.quantity&&p.quantity>available(product,p.date,orders))errors.push('Not enough capacity for this date');
 return {product,errors,total:product&&p.quantity?product.price*p.quantity:0};
}
export function commitOrder(p:Proposal,catalog:Product[],orders:Order[],customer:string,messageId:string):Order[]{
 if(p.intent!=='order')throw new Error('Only an order request can be reserved.');
 if(orders.some(o=>o.messageId===messageId))throw new Error('This message already has an order.');
 const check=inspect(p,catalog,orders);if(check.errors.length)throw new Error(check.errors[0]);
 return [...orders,{id:'MD-'+String(1001+orders.length),messageId,customer,productId:p.productId!,quantity:p.quantity!,date:p.date!,total:check.total,paid:0,status:'reserved'}];
}
export function matchesReservation(p:Proposal,order:Order){return p.productId===order.productId&&p.quantity===order.quantity&&p.date===order.date;}
export function reservationReview(p:Proposal,catalog:Product[],orders:Order[],messageId:string){
 const order=orders.find(o=>o.messageId===messageId)||null;
 const changed=!!order&&!matchesReservation(p,order);
 const remainingOrders=order?orders.filter(o=>o.id!==order.id):orders;
 const check=inspect(p,catalog,remainingOrders);
 if(order&&!changed)check.total=order.total;
 if(order&&order.status!=='reserved')check.errors.push(`This order is ${order.status}; manage its status in Orders.`);
 if(order&&changed&&check.total<order.paid)check.errors.push('New total is below the payment already recorded. Review the payment first.');
 return {order,changed,remainingOrders,check};
}
export function updateReservation(p:Proposal,catalog:Product[],orders:Order[],messageId:string):Order[]{
 if(p.intent!=='order')throw new Error('Only an order request can be reserved.');
 const review=reservationReview(p,catalog,orders,messageId);
 if(!review.order)throw new Error('Reservation not found.');
 if(!review.changed)return orders;
 if(review.check.errors.length)throw new Error(review.check.errors[0]);
 return orders.map(o=>o.id===review.order!.id?{...o,productId:p.productId!,quantity:p.quantity!,date:p.date!,total:review.check.total}:o);
}
export function recordPayment(order:Order,amount:number):Order{
 if(order.status==='cancelled')throw new Error('Cancelled order cannot receive payments');
 const cents=Math.round(amount*100), paidCents=Math.round(order.paid*100),totalCents=Math.round(order.total*100);
 if(!Number.isFinite(amount)||cents<=0||Math.abs(amount*100-cents)>0.000001||cents>totalCents-paidCents)throw new Error('Enter an amount within the outstanding balance.');
 return {...order,paid:(paidCents+cents)/100};
}
export function businessDate(now=new Date()){return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Kolkata',year:'numeric',month:'2-digit',day:'2-digit'}).format(now);}
export function nextDate(date:string){const d=new Date(date+'T12:00:00Z');d.setUTCDate(d.getUTCDate()+1);return d.toISOString().slice(0,10);}
export function sampleParse(text:string,referenceDate=businessDate()):Proposal{
 const t=text.toLowerCase();const language=/\b(hai|chahiye|kal|ka|kya|bhai|milega|kar|chahie)\b/.test(t)?'hi':'en';
 const productId=/red\s?velvet/.test(t)?'redvelvet':/chocol|truffle/.test(t)?'chocolate':/cupcake/.test(t)?'cupcakes':/vanilla/.test(t)?'vanilla':null;
 const intent=/\b(book|order|reserve|chahiye|chahie|need|want|kar\s+do)\b/.test(t)?'order':productId||/menu|catalog|price|rate|available/.test(t)?'question':'handoff';
 const explicit=t.match(/\b(\d+)\s*(?:(?:chocolate|truffle|vanilla|red\s*velvet)\s+)?(?:boxes|box|cakes|cake|packs)\b/);const quantity=explicit?Number(explicit[1]):null;
 const date=t.match(/\d{4}-\d{2}-\d{2}/)?.[0]??(/tomorrow|\bkal\b/.test(t)?nextDate(referenceDate):/today|\baaj\b/.test(t)?referenceDate:null);
 return {intent,productId,quantity,date,language,note:`Sample parser · reference date ${referenceDate} (India). Owner checks every detail.`,missing:[...(!productId?['Product']:[]),...(!quantity?['Quantity']:[]),...(!date?['Pickup date']:[])]};
}
export function replyFor(p:Proposal,catalog:Product[],orders:Order[],reservation?:Order|null,previous?:Order|null){
 const product=catalog.find(x=>x.id===p.productId);const hi=p.language==='hi';
 if(reservation&&matchesReservation(p,reservation)&&reservation.status==='reserved'&&product){
 const pending=Math.max(0,Math.ceil(reservation.total/2)-reservation.paid);
 const revised=previous&&!matchesReservation(p,previous);
 const previousProduct=previous&&catalog.find(x=>x.id===previous.productId);
 const change=revised?(hi?`Order ${reservation.id} update hua: pehle ${previous.quantity} × ${previousProduct?.name||previous.productId}, pickup ${previous.date}, total ₹${previous.total}; ab neeche wali details final hain. `:`Order ${reservation.id} updated: previously ${previous.quantity} × ${previousProduct?.name||previous.productId}, pickup ${previous.date}, total ₹${previous.total}; the details below replace that reservation. `):'';
 return change+(hi?`Aapka order ${reservation.id} reserve ho gaya hai 🙂 ${reservation.quantity} × ${product.name} (${product.unit}), pickup ${reservation.date}. Total ₹${reservation.total}.${pending?` Booking advance mein ₹${pending} baaki hai.`:''}`:`Your order ${reservation.id} is reserved 🙂 ${reservation.quantity} × ${product.name} (${product.unit}), pickup ${reservation.date}. Total ₹${reservation.total}.${pending?` Booking advance remaining: ₹${pending}.`:''}`);
 }
 if(reservation)orders=orders.filter(o=>o.id!==reservation.id);
 if(p.intent==='handoff')return hi?'Main yeh detail check karke aapko batata hoon. Thoda waqt dijiye 🙂':'Let me check that detail and get back to you 🙂';
 if(!product)return (hi?'Hello! Hamara menu: ':'Hello! Here’s our menu: ')+catalog.map(x=>`${x.name} (${x.unit}) ₹${x.price}`).join('; ')+(hi?'. Kaunsa item aur pickup date chahiye?':'. Which item and pickup date would you like?');
 if(p.date&&available(product,p.date,orders)<(p.quantity??1)){
 const options=alternativesFor(p,catalog,orders);const quantity=p.quantity??1;
 const intro=hi?`Sorry, ${p.date} ko ${quantity} × ${product.name} available nahi hai. `:`Sorry, ${quantity} × ${product.name} is unavailable on ${p.date}. `;
 if(!options.length)return intro+(hi?'Is quantity ke liye koi similar item bhi available nahi hai. Koi doosri pickup date chalegi?':'No similar item has enough availability for this quantity. Would another pickup date work?');
 const menu=options.map(x=>`${x.name} (${x.unit}) — ₹${x.price}${quantity>1?` each; ${quantity} total ₹${x.price*quantity}`:''}`).join('; ');
 return intro+(hi?`Usi date ke liye yeh options available hain: ${menu}. Kaunsa pasand karenge? Aapke choose karne ke baad booking confirm karenge 🙂`:`These alternatives are available for the same date: ${menu}. Which would you prefer? We’ll confirm the booking after you choose 🙂`);
 }
 const total=product.price*(p.quantity??1);
 if(p.intent==='order'&&p.quantity&&p.date)return hi?`Aapke liye quote: ${p.quantity} × ${product.name} (${product.unit}), pickup ${p.date}. Total ₹${total}; booking advance ₹${Math.ceil(total/2)}. Abhi booking confirm nahi hui hai. Yeh details sahi hain? 🙂`:`Your quote: ${p.quantity} × ${product.name} (${product.unit}), pickup ${p.date}. Total ₹${total}; booking advance ₹${Math.ceil(total/2)}. This is not yet a confirmed booking. Are these details correct? 🙂`;
 return hi?`${product.name} (${product.unit}) ₹${product.price} ka hai. ${p.quantity?'':'Kitne chahiye? '}${p.date?'':'Pickup kis date ko chahiye? '}`:`${product.name} (${product.unit}) is ₹${product.price}. ${p.quantity?'':'How many would you like? '}${p.date?'':'What is your pickup date? '}`;
}
