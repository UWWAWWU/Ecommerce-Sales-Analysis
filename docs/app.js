/* Static dashboard: all filtering happens in the browser on pre-aggregated data. */
(() => {
  const data = window.RETAIL_DATA;
  const byId = id => document.getElementById(id);
  if (!data) { byId('status').textContent = 'Dashboard data is unavailable. Run python src/build.py to rebuild it.'; return; }
  const country = byId('country'), from = byId('from'), to = byId('to');
  const money = n => new Intl.NumberFormat('en-GB', {style:'currency', currency:'GBP', minimumFractionDigits:2, maximumFractionDigits:2}).format(n);
  const compact = n => n >= 1e6 ? `£${(n / 1e6).toFixed(2)}m` : n >= 1e3 ? `£${(n / 1e3).toFixed(1)}k` : money(n);
  const integer = n => new Intl.NumberFormat('en-GB').format(n);
  const monthLabel = s => new Date(`${s}-01T12:00:00Z`).toLocaleString('en-GB',{month:'short', year:'numeric', timeZone:'UTC'});
  for (const name of data.countries) country.add(new Option(name, name));
  for (const month of data.months) { from.add(new Option(monthLabel(month),month)); to.add(new Option(monthLabel(month),month)); }
  from.value = data.months[0]; to.value = data.months.at(-1);

  function rank(container, entries, valueKey) {
    container.replaceChildren();
    if (!entries.length) { const p=document.createElement('p'); p.className='empty'; p.textContent='No sales in this selection.'; container.append(p); return; }
    const maximum = entries[0][valueKey];
    entries.slice(0,7).forEach((row,i) => {
      const item=document.createElement('div'); item.className='rank-row';
      const left=document.createElement('div'); const name=document.createElement('div'); name.className='rank-name';
      name.textContent=`${String(i+1).padStart(2,'0')}  ${row.label}`; name.title=row.label;
      const track=document.createElement('div'); track.className='bar-track';
      const bar=document.createElement('div'); bar.className='bar'; bar.style.width=`${100*row[valueKey]/maximum}%`;
      track.append(bar); left.append(name,track);
      const value=document.createElement('div'); value.className='rank-value'; value.textContent=compact(row[valueKey]);
      item.append(left,value); container.append(item);
    });
  }

  function trend(monthly) {
    const el=byId('trend'); el.replaceChildren();
    const values=data.months.filter(m => m>=from.value && m<=to.value).map(m => ({month:m,value:monthly.get(m)||0}));
    if (!values.some(d=>d.value)) { el.textContent='No sales in this selection.'; return; }
    const w=720,h=250, l=63,r=17,t=20,b=39, plotW=w-l-r,plotH=h-t-b;
    const max=Math.max(...values.map(d=>d.value))*1.12;
    const x=i => l+(values.length===1 ? plotW/2 : i*plotW/(values.length-1));
    const y=v => t+plotH*(1-v/max);
    const points=values.map((d,i)=>`${x(i)},${y(d.value)}`).join(' ');
    const area=`M${x(0)} ${t+plotH} L${values.map((d,i)=>`${x(i)} ${y(d.value)}`).join(' L')} L${x(values.length-1)} ${t+plotH} Z`;
    let svg=`<svg viewBox="0 0 ${w} ${h}" preserveAspectRatio="none" aria-hidden="true"><defs><linearGradient id="areaFade" x1="0" y1="0" x2="0" y2="1"><stop stop-color="#b9ed79" stop-opacity=".29"/><stop offset="1" stop-color="#b9ed79" stop-opacity="0"/></linearGradient></defs>`;
    for(let k=0;k<=3;k++){const yy=t+plotH*k/3;svg+=`<line class="grid" x1="${l}" x2="${w-r}" y1="${yy}" y2="${yy}"/><text x="${l-10}" y="${yy+4}" text-anchor="end">${compact(max*(1-k/3))}</text>`;}
    svg+=`<path class="area" d="${area}"/><polyline class="line" points="${points}"/>`;
    values.forEach((d,i)=>{svg+=`<circle cx="${x(i)}" cy="${y(d.value)}" r="4"><title>${monthLabel(d.month)}: ${money(d.value)}</title></circle>`;
      if(values.length<=7||i===0||i===values.length-1||i%2===0) svg+=`<text x="${x(i)}" y="${h-8}" text-anchor="middle">${d.month.slice(5)}/${d.month.slice(2,4)}</text>`;
    });
    svg+='</svg>';el.innerHTML=svg;
    el.setAttribute('aria-label', `Monthly gross sales from ${monthLabel(values[0].month)} to ${monthLabel(values.at(-1).month)}. Peak ${money(Math.max(...values.map(d=>d.value)))}.`);
  }

  function render() {
    if(from.value>to.value) { if(document.activeElement===from) to.value=from.value; else from.value=to.value; }
    const inRange = r => r.month>=from.value && r.month<=to.value;
    const visible = r => inRange(r) && (country.value==='all'||r.country===country.value);
    const rows=data.geography.filter(visible);
    const total=rows.reduce((a,r)=>({revenue:a.revenue+r.revenue,orders:a.orders+r.orders,cancelledOrders:a.cancelledOrders+r.cancelledOrders,lines:a.lines+r.lines}),{revenue:0,orders:0,cancelledOrders:0,lines:0});
    byId('revenue').textContent=money(total.revenue);
    byId('orders').textContent=integer(total.orders);
    byId('aov').textContent=total.orders?money(total.revenue/total.orders):'—';
    byId('cancel-rate').textContent=total.orders+total.cancelledOrders ? `${(100*total.cancelledOrders/(total.orders+total.cancelledOrders)).toFixed(2)}%` : '—';
    byId('cancel-count').textContent=integer(total.cancelledOrders);
    byId('status').textContent=`${country.value==='all'?'All markets':country.value} · ${monthLabel(from.value)} – ${monthLabel(to.value)} · ${integer(total.lines)} sales lines`;

    const monthly=new Map(), markets=new Map();
    rows.forEach(r=>{monthly.set(r.month,(monthly.get(r.month)||0)+r.revenue);markets.set(r.country,(markets.get(r.country)||0)+r.revenue);});
    trend(monthly);
    rank(byId('markets'),Array.from(markets,([label,revenue])=>({label,revenue})).sort((a,b)=>b.revenue-a.revenue),'revenue');

    const productTotals=new Map();
    data.products.forEach(r=>{if(visible(r))productTotals.set(r.code,(productTotals.get(r.code)||0)+r.revenue);});
    const top=Array.from(productTotals,([code,revenue])=>({label:`${data.productNames[code]||code} · ${code}`,revenue})).sort((a,b)=>b.revenue-a.revenue);
    rank(byId('products'),top,'revenue');
    const allMarketRevenue=data.geography.filter(inRange).reduce((sum,row)=>sum+row.revenue,0);
    const shareRevenue=country.value==='all' ? (markets.get('United Kingdom')||0) : total.revenue;
    byId('share').textContent=allMarketRevenue?`${(100*shareRevenue/allMarketRevenue).toFixed(1)}%`:'—';
    byId('share-label').textContent=country.value==='all'
      ? 'UK share of selected gross sales'
      : `${country.value} share of all-market gross sales in the selected period`;
  }
  [country,from,to].forEach(el=>el.addEventListener('change',render));
  byId('reset').addEventListener('click',()=>{country.value='all';from.value=data.months[0];to.value=data.months.at(-1);render();});
  render();
})();
