import{$ as de,A as be,Aa as at,B as f,Ba as rt,C as ee,Ca as ot,D as L,Da as it,E as Be,Ea as we,Fa as w,G as x,Ga as ke,H as Ae,Ha as lt,I as Oe,Ia as ct,J as te,Ja as dt,K as O,L as ie,M as le,Ma as ut,N as z,Na as pt,Oa as mt,Pa as ht,U as Pe,V as R,X as ye,Y as ce,Z as Ke,_ as V,aa as m,ba as T,c as De,ca as H,d as a,da as E,e as y,ea as P,f as C,fa as Ue,g as U,ga as je,h as Y,ha as Fe,ia as Ge,ja as Ve,k as J,ka as qe,l as b,la as We,m as Q,ma as Xe,n as Z,na as q,oa as j,pa as Ye,q as re,qa as Je,r as _e,ra as Qe,s as oe,sa as Ze,t as h,ta as ue,ua as et,v as N,va as pe,w as Ne,wa as tt,x as ze,xa as nt,y as Re,ya as st,z as He,za as me}from"./chunks/chunk-NBCTQRJG.js";import"./chunks/chunk-EBVYA7LM.js";import"./chunks/chunk-VC46IEJQ.js";var M=new J(Q("sidebar",!0)),I=new J(null),B=new J(!1),W=new J(null);M.subscribe(e=>Z("sidebar",e));var $t=Q("visit",Date.now());Z("visit",Date.now());function ft(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var he=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var Ut=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function xe(e){W.set(e),Pe.set(e.theme),e.settings?.theme_mode&&R.set(e.settings.theme_mode),ye()}async function Te(e,t){e==="theme_mode"&&(R.set(t),ye()),xe(await We(e,t))}function gt(){let e=b(R),t=V(),s=b(W),[n,r]=y(null);C(()=>{document.title="Settings \xB7 Beamtime"},[]);let o=(i,p)=>{r(null),Te(i,p).catch(d=>r(d.message))},l=s?.settings??{};return a`<div class="page settings">
    <header class="header"><h1 class="title" tabindex="-1">Settings</h1></header>
    <p class="muted small">Changes are written to <code>${l.file??"beamtime.yaml"}</code>, the project's settings.</p>
    ${n?a`<${H} kind="error">${n}<//>`:null}
    <h2>Appearance</h2>
    <div class="settings-rows">
      <span class="field-label">Mode</span>
      <div class="segmented" role="radiogroup" aria-label="Theme mode">
        ${Ut.map(([i,p,d])=>a`<button type="button" role="radio" aria-checked=${e===i} onClick=${()=>o("theme_mode",i)}>
          <${m} name=${p} size=${15} />${d}</button>`)}
      </div>
      <span class="field-label">Theme</span>
      <select value=${l.theme} onChange=${i=>o("theme",i.target.value)}>
        ${(s?.themes??[]).map(i=>a`<option value=${i}>${i}</option>`)}
      </select>
    </div>
    <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files go in <code>themes/</code> next to beamtime.yaml.</p>
    ${(s?.theme?.problems??[]).map(i=>a`<${H} kind="warning">${i}<//>`)}
    <h2>Figures</h2>
    <div class="settings-rows">
      <span class="field-label">Style sheets</span>
      ${(s?.figure_styles??[]).length?a`<${Xe} options=${s.figure_styles} value=${l.figure_style??[]} label="Style sheets"
            placeholder="Add a style" onChange=${i=>o("figure_style",i)} />`:a`<span class="muted small"><code>${JSON.stringify(l.figure_style??[])}</code>; choosing others needs the figures
            extra: <code>uv add matplotlib scienceplots</code></span>`}
    </div>
    <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(l.figure_style??[])})</code>, in this order
      (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>.</p>
    <h2>Keyboard</h2>
    <table class="kv">${he.map(([i,p])=>a`<tr><td><kbd>${i}</kbd></td><td>${p}</td></tr>`)}</table>
    <h2>About</h2>
    <table class="kv">
      <tr><td class="muted">version</td><td>${s?.version}</td></tr>
      <tr><td class="muted">root</td><td><code>${s?.root}</code></td></tr>
      <tr><td class="muted">log dir</td><td><code>${s?.logdir}</code></td></tr>
    </table>
  </div>`}var vt={system:"light",light:"dark",dark:"system"},jt={system:"monitor",light:"sun",dark:"moon"};function bt(){let e=b(W),t=b(R),s=b(M);return a`<header class="topbar">
    <${P} icon="panel-left" label=${s?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${s} onClick=${()=>M.set(!s)} />
    <a class="project" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search" onClick=${()=>I.set("")} aria-label="Search (⌘K)">
      <${m} name="search" size=${15} /><span class="search-label">Search groups, runs, commands</span><kbd>⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <span class="source" data-tip="Sources: this machine. Remote sources come later."><${m} name="server" size=${15} /> local</span>
      <${P} icon=${jt[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${vt[t]})`}
        onClick=${()=>{Te("theme_mode",vt[t])}} />
      <a class="icon-button" href=${it(L.value.page==="group"?L.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${m} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${m} name="settings" size=${16} /></a>
    </div>
  </header>`}function Ft(e){let[t,s]=y(Date.now());return C(()=>{let n=setInterval(()=>s(Date.now()),e);return()=>clearInterval(n)},[e]),t}function Gt(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function yt(){let e=b(Ne),t=b(N),s=b(ze),n=b(L),r=Ft(5e3),o=h(st()).data,l=E(h(me()).data),i=b(W),p=o?.daemon,d=o?.runs?.running??0,u=l.filter(k=>k["run.status"]==="failed"&&Gt(k["run.ended_at"])>$t).length,g=o?.meta?.freshness,[$,D,v]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&p?["",`live \xB7 updated ${z(new Date(s).toISOString(),r)}`,`beamtime serve, pid ${p.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return a`<footer class="statusbar">
    <span class="status-item" data-tip=${v}><span class=${`live-dot ${$}`}></span>${D}</span>
    ${d?a`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>I.set("running")}>
          <${m} name="circle-dot" size=${14} class="tone-running" />${d} running</button>`:null}
    ${u?a`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>I.set("failed")}>
          <${m} name="circle-x" size=${14} />${u} failed since your last visit</button>`:null}
    ${g?.behind?a`<span class="status-item warn-text" data-tip=${g.text}><${m} name="hourglass" size=${14} />${g.behind} runs behind</span>`:null}
    ${g?.damaged?.length?a`<span class="status-item warn-text" data-tip=${g.damaged.join(`
`)}><${m} name="triangle-alert" size=${14} />${g.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${n.page==="group"&&n.run?a`<span class="status-item"><${m} name="activity" size=${14} />1 run selected</span>`:null}
    <${P} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>N.set(!t)} />
    ${i?.outdated?a`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item subtle">${i?.version?`beamtime ${i.version}`:""}</span>
  </footer>`}function wt(e){let t=()=>x(f(e.path),{replace:!0});return a`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head">
      <span class="status-item"><${m} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${P} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?a`<${Vt} id=${e.run} scope=${e.path} />`:a`<${qt} path=${e.path} />`}
  </aside>`}function Vt({id:e,scope:t}){let s=h(ue(e,t)).data,n=h(et(e,t)).data,r=h(pe(t)).data,o=V(),l=Y(()=>de(E(r).map(d=>d["run.id"]),o).get(e),[r,o,e]);if(!s)return a`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let i=s.run,p=Object.entries(s.metrics??{});return a`<div class="drawer-body">
    <h3><span class="run-dot" style=${`background:${l??"var(--bt-subtle)"}`}></span>
      <a href=${ee(e)}>${i.name}</a></h3>
    <p class="facts small">
      <${T} spec=${w("run",i.status)} word />
      <span class="fact"><b>${ie(i.steps)}</b> steps</span>
      <span class="fact"><b>${le(i.duration_s)}</b></span>
      <span class="fact" data-tip=${i.created_at}>${z(i.created_at)}</span>
    </p>
    ${i.error?a`<pre class="log bad-text">${i.error}</pre>`:null}
    <h4>Config</h4>
    <table class="kv">${Object.entries(s.config??{}).map(([d,u])=>a`<tr><td>${d}</td><td class="num">${O(u)}</td></tr>`)}</table>
    ${p.length?a`<h4>Metrics</h4>
          <table class="kv">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${p.map(([d,u])=>a`<tr><td>${d}</td><td class="num"><b>${O(u.last)}</b></td>
              <td class="num">${O(u.min)}</td><td class="num">${O(u.max)}</td></tr>`)}
          </table>`:null}
    ${s.cited_by?.length?a`<h4>Cited by</h4>${s.cited_by.map(d=>a`<p class="small"><${T} spec=${w("note",d.type)} /> ${d.description}</p>`)}`:null}
    <h4>Events</h4>
    ${(s.events??[]).slice(-8).map(d=>a`<div class="event"><span class="muted num">${d.t?.slice(5,16).replace("T"," ")}</span>
        <${m} name=${ke(d.type)} size=${14} /><span>${d.description}</span></div>`)}
    <h4>Output</h4>
    <pre class="log">${(n?.lines??[]).join(`
`)}</pre>
  </div>`}function qt({path:e}){let t=h(tt(e)).data,s=h(nt(e)).data;return a`<div class="drawer-body">
    <h4 style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?a`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(n=>!String(n.state??"").startsWith("superseded")).map(n=>a`<${dt} key=${n.id} note=${n} />`)}</div>
    <h4>Timeline</h4>
    ${(s?.entries??[]).slice().reverse().map(n=>a`<div class="event"><span class="muted num">${n.t?.slice(5,16).replace("T"," ")}</span>
        <${m} name=${n.kind==="note"?"file-text":ke(n.type)} size=${14} />
        <span>${n.run?a`<a href=${ee(n.run)}>${n.run.slice(-8)}</a> `:null}${n.description??n.type}</span></div>`)}
  </div>`}var Se=["failed","killed","lost"];function Ee(e){let t=e.path==="."?[]:e.path.split("/"),s=t.length&&be(t[t.length-1])?t[t.length-1]:null,n=t.slice(0,-1);return a`<header class="header">
    <nav class="crumbs" aria-label="Breadcrumb">
      ${t.length?a`<a href=${f(".")}>local</a>`:null}
      ${n.map((r,o)=>a`<span class="sep">/</span><a href=${f(n.slice(0,o+1).join("/"))}>${r}</a>`)}
    </nav>
    ${s?a`<${Xt} id=${s} scope=${e.path} />`:a`<${Wt} path=${e.path} />`}
    ${e.finding?a`<p class="finding">${e.finding}</p>`:null}
  </header>`}function Wt({path:e}){let t=E(h(Je(e)).data)[0]??null,s=h(t?.proposal?Qe(e):null).data,n=h(t?.proposal?Ze(e):null).data,r=n?.proposal?.rationale,o=n?.versions?.find(u=>u.version===n.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,l=e==="."?"local":e.split("/").pop();if(!t)return a`<h1 class="title" tabindex="-1">${l}</h1><div class="skeleton late" style="block-size: 52px"></div>`;let[i,p]=ct(s?.progress?.text??t.progress),d=Se.reduce((u,g)=>u+(t[g]??0),0);return a`
    <h1 class="title" tabindex="-1">${l} <${T} spec=${w("research",t.status)} word /></h1>
    ${t.proposal?a`<div class="statement">
          <${we} value=${t.proposal} label="the proposal's statement" locked=${n?o:"Loading the proposal\u2026"}
            render=${u=>a`<span data-tip=${o?void 0:r}>${u}</span>`}
            onSave=${u=>Fe(e,u)} />
        </div>`:null}
    ${t.proposal?a`<div class="preds">
          ${(s?.predictions??[]).map(u=>a`<span class="pred" key=${u.name} data-tip=${lt(u)}>
              <${T} spec=${w("result",u.result)} /><b>${u.name}</b></span>`)}
          ${s?.provisional?a`<span class="tag tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
          ${i?a`<span class="pred"><${Ue} fraction=${s?.progress?.fraction??null} label=${p??i} />
                <span data-tip=${p}>${i}</span></span>`:null}
          ${t.verdict?a`<span class="pred"><${T} spec=${w("verdict",t.verdict)} word /></span>`:null}
        </div>`:null}
    <div class="facts">
      <span class="fact"><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?a`<span class="fact"><${T} spec=${w("run","running")} /><b>${t.running}</b> running</span>`:null}
      ${t.finished?a`<span class="fact"><${T} spec=${w("run","finished")} /><b>${t.finished}</b> finished</span>`:null}
      ${d?a`<span class="fact tone-bad" data-tip=${Se.filter(u=>t[u]).map(u=>`${t[u]} ${u}`).join(", ")}>
            <${m} name="circle-x" size=${15} /><b class="tone-bad">${d}</b> ${d===1?Se.find(u=>t[u]):"ended early"}</span>`:null}
      ${t.notes?a`<span class="fact"><${m} name="file-text" size=${15} /><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${kt} path=${e} />
    </div>`}function Xt({id:e,scope:t}){let s=h(ue(e,t)).data;if(!s)return a`<h1 class="title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 52px"></div>`;let n=s.run,r=()=>{navigator.clipboard?.writeText(n.id)};return a`
    <h1 class="title" tabindex="-1"><${we} value=${n.name??n.id} label="the run's name" class="title-edit"
        onSave=${o=>Ge(n.id,t,o.trim())} />
      <${T} spec=${w("run",n.status)} word /></h1>
    ${n.error?a`<p class="statement bad-text" data-tip=${n.error}>${n.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span class="fact"><b>${ie(n.steps)}</b> steps</span>
      <span class="fact"><b>${le(n.duration_s)}</b></span>
      <span class="fact" data-tip=${n.created_at}>${z(n.created_at)}</span>
      <${kt} path=${t} />
      <span class="fact">
        <${P} icon="copy" label=${`Copy the run id ${n.id}`} onClick=${r} />
        <${je} icon="ellipsis" label="Details" title="Run details" class="run-details">
          <table class="kv">${Yt(n).map(([o,l])=>a`<tr><td class="muted">${o}</td><td>${l}</td></tr>`)}</table>
          <div class="menu-list">
            <button type="button" onClick=${()=>x(f(t,{run:n.id}),{replace:!0})}>
              <${m} name="panel-right" size=${15} /> Open in the side panel</button>
            <button type="button" onClick=${r}><${m} name="copy" size=${15} /> Copy the run id</button>
            ${n.git?.commit?a`<button type="button" onClick=${()=>navigator.clipboard?.writeText(n.git.commit)}>
              <${m} name="git-commit" size=${15} /> Copy the commit</button>`:null}
          </div>
        <//>
      </span>
    </div>
    ${(s.proposals??[]).length?a`<div class="preds" style="margin-block-start: 10px">
          ${s.proposals.map(o=>a`<a class="pred" href=${f(o.group)} data-tip=${o.statement}>
              <${T} spec=${w("result",o.check)} /><b>${o.group==="."?"own proposal":o.group}</b>
              ${o.verdict?a`<${T} spec=${w("verdict",o.verdict)} />`:null}</a>`)}
        </div>`:null}`}function kt({path:e}){let t=h(Ye(e)).data?.summary;if(!t)return null;let s=Object.entries(t.config??{}).map(([r,o])=>`${r} ${O(o)}`).join(", "),n=be(e.split("/").pop()??"");return a`<span class="fact" data-tip=${`${t.stat} of ${t.metric} over ${n?"the run":"all runs"}`}>
    best <b>${t.metric} ${O(t.value)}</b>
    ${n?null:a`<span>· <a href=${ee(t.run)}>${t.name}</a>${s?a` <em>(${s})</em>`:null}</span>`}
  </span>`}function Yt(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(s=>!!s[1]).map(([s,n])=>[s,String(n)])}function xt(e,t){let s=e.split(`
`),n=t.split(`
`),r=s.length,o=n.length,l=Array.from({length:r+1},()=>new Uint32Array(o+1));for(let u=r-1;u>=0;u--)for(let g=o-1;g>=0;g--)l[u][g]=s[u]===n[g]?l[u+1][g+1]+1:Math.max(l[u+1][g],l[u][g+1]);let i=[],p=0,d=0;for(;p<r&&d<o;)s[p]===n[d]?(i.push({kind:"same",text:s[p]}),p++,d++):l[p+1][d]>=l[p][d+1]?i.push({kind:"removed",text:s[p++]}):i.push({kind:"added",text:n[d++]});for(;p<r;)i.push({kind:"removed",text:s[p++]});for(;d<o;)i.push({kind:"added",text:n[d++]});return i}function Tt(e,t=3){let s=[],n=0;for(;n<e.length;){if(e[n].kind!=="same"){s.push(e[n++]);continue}let r=n;for(;r<e.length&&e[r].kind==="same";)r++;let o=n===0?0:t,l=r===e.length?0:t;r-n>o+l+1?s.push(...e.slice(n,n+o),{kind:"skip",count:r-n-o-l},...e.slice(r-l,r)):s.push(...e.slice(n,r)),n=r}return s}function $e(e){let t=h(pe(e.path)),s=V(),n=E(t.data),r=Y(()=>de(n.map(i=>i["run.id"]),s),[t.data,s]),o=Y(()=>new Map(n.map(i=>[i["run.id"],i["run.name"]??i["run.id"]])),[t.data]);if(!e.view)return a`<div class="view"><div class="skeleton late" style="block-size: 320px"></div></div>`;let l={path:e.path,colors:r,names:o,metrics:e.view.metrics??{}};return a`<div class="view"><${Ke.Provider} value=${l}><${ht} node=${e.view.view} /><//></div>`}function St(e){let t=e.view,s=b(L),n=s.page==="group"&&s.version,r=t.versions?a`<a href=${f(e.path,{history:!0})}><${m} name="history" size=${14} /> history (${t.versions})</a>`:null,o;switch(t.source){case"draft":o=a`draft <b>${t.draft}</b>`;break;case"view":o=a`${t.title?a`<em>${t.title}</em> · `:null}saved ${z(Ce(t.version))} by ${t.author??"unknown"}`;break;default:o=a`the built-in view`}return a`<div class="view-source">
    <${m} name="layout" size=${14} /><span>${o}</span>
    ${n?a`<a href=${f(e.path)}>an older version · show the current one</a>`:null}
    ${r}
    ${t.source==="draft"||n?null:a`<${Jt} path=${e.path} />
        <${Qt} path=${e.path} view=${t} />`}
  </div>`}function Jt(e){let[t,s]=y(null);return a`<button type="button" class="link small" onClick=${async()=>{s(null);try{qe.set(await Ve(e.path,null,""))}catch(r){s(r.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${m} name="file-text" size=${14} /> add text</button>
    ${t?a`<span class="bad-text small">${t}</span>`:null}`}function Qt(e){let t=ut(e.path),s=mt(t),[n,r]=y(!1),[o,l]=y(e.view.title??""),[i,p]=y(e.view.finding??""),[d,u]=y(null),[g,$]=y(!1);if(!s&&!n)return null;let D=async v=>{v.preventDefault(),$(!0),u(null);try{let k={charts:t.charts,added:t.added,order:t.order,spans:t.spans};await re("save_view",{path:e.path,prefs:k,title:o,finding:i}),pt(e.path,()=>({view:{},charts:{},added:[],order:{},spans:{}})),He(G=>["view","view_history","summary"].includes(G.method)&&G.scope===e.path),r(!1)}catch(k){u(k.message)}finally{$(!1)}};return n?a`<form class="save-form" onSubmit=${D}>
    <label class="field"><span class="field-label">Title</span>
      <input value=${o} onInput=${v=>l(v.target.value)} /></label>
    <label class="field"><span class="field-label">Finding</span>
      <input value=${i} placeholder="the key result in one sentence"
        onInput=${v=>p(v.target.value)} /></label>
    <div class="save-actions">
      <button type="submit" class="button primary" disabled=${g}>${g?"Saving\u2026":"Save as view"}</button>
      <button type="button" class="link small" onClick=${()=>r(!1)}>cancel</button>
      ${d?a`<span class="bad-text small">${d}</span>`:null}
    </div>
  </form>`:a`<button type="button" class="link small save-view" onClick=${()=>r(!0)}
        data-tip="Save your chart settings and added charts as this page's view, for everyone">
      <${m} name="save" size=${14} /> Save as view</button>`}function Et(e){let t=h(rt(e.path)),s=t.data?.entries??[],[n,r]=y(null),o=n??s.slice(0,2).map(i=>i.version).reverse(),l=i=>{let p=o.includes(i)?o.filter(d=>d!==i):[...o,i].slice(-2);r(p.sort())};return t.status==="error"?a`<${H} kind="error">${t.error}<//>`:a`<section class="history">
    <h2 class="history-title"><${m} name="history" size=${18} /> View history</h2>
    ${t.data&&!s.length?a`<${H}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${s.map((i,p)=>a`<li key=${i.version} class=${o.includes(i.version)?"picked":""}>
          <label><input type="checkbox" checked=${o.includes(i.version)} onChange=${()=>l(i.version)} />
            <span class="num muted" data-tip=${i.version}>${z(i.time)}</span>
            <b>${i.title??"untitled"}</b><span class="muted">${i.author??""}</span>
            ${i.message?a`<span>${i.message}</span>`:null}</label>
          <a href=${p===0?f(e.path):f(e.path,{version:i.version})}
            onClick=${d=>{d.preventDefault(),x(p===0?f(e.path):f(e.path,{version:i.version}))}}>${p===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${o.length===2?a`<${Zt} path=${e.path} a=${o[0]} b=${o[1]} />`:null}
  </section>`}function Zt(e){let t=i=>({method:"view_show",params:{group:e.path,version:i},scope:e.path}),s=h(t(e.a)).data,n=h(t(e.b)).data,r=h(j(e.path,e.a)).data,o=h(j(e.path,e.b)).data,l=s&&n?Tt(xt(s.yaml,n.yaml)):[];return a`<div class="compare">
    <h3 class="block-title">Changes from ${z(Ce(e.a))} to ${z(Ce(e.b))}</h3>
    <pre class="diff">${l.map(i=>i.kind==="skip"?a`<div class="diff-skip">⋯ ${i.count} unchanged lines</div>`:a`<div class=${`diff-${i.kind}`}>${i.kind==="added"?"+ ":i.kind==="removed"?"\u2212 ":"  "}${i.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title">${r?.title??e.a}</h3><${$e} path=${e.path} view=${r} /></div>
      <div><h3 class="block-title">${o?.title??e.b}</h3><${$e} path=${e.path} view=${o} /></div>
    </div>
  </div>`}function Ce(e){return e?`${e.slice(0,4)}-${e.slice(4,6)}-${e.slice(6,8)}T${e.slice(9,11)}:${e.slice(11,13)}:${e.slice(13,15)}Z`:null}function Ct(e){return C(()=>{document.title=`${e.path==="."?"local":e.path} \xB7 Beamtime`},[e.path]),e.history?a`<div class="page"><${Ee} path=${e.path} /><${Et} path=${e.path} /></div>`:a`<div class="page">
    <${en} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function en(e){let t=h(j(e.path,e.version,e.draft));return C(()=>{t.status==="ready"&&requestAnimationFrame(Ae)},[t.status==="ready"]),a`
    <${Ee} path=${e.path} finding=${t.data?.finding} />
    ${t.data?a`<${St} path=${e.path} view=${t.data} />`:null}
    ${t.status==="error"?a`<${H} kind="error">${t.error}<//>`:a`<${$e} path=${e.path} view=${t.data} />`}`}function Lt(e){C(()=>{oe(j(e.id)).then(s=>x(f(s.path),{replace:!0})).catch(()=>{})},[e.id]);let t=h(j(e.id));return t.status==="error"?a`<div class="page"><${H} kind="error">${t.error}<//></div>`:a`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}function Mt(e,t){let s=e.toLowerCase(),n=t.toLowerCase();if(!s)return 1;let r=n.indexOf(s);if(r>=0)return 100-Math.min(r,50)-n.length/100;let o=0,l=0;for(let i of n)if(i===s[o]?o++:o>0&&l++,o===s.length)return 40-Math.min(l,39);return 0}function Dt(e){let[t,s]=y(e.query),[n,r]=y(0),o=U(null),l=E(h(q()).data),i=E(h(me()).data);C(()=>{let c=o.current;c.showModal();let _=()=>I.set(null);c.addEventListener("close",_);let K=!1,se=A=>{let ae=c.getBoundingClientRect();return A.clientX<ae.left||A.clientX>ae.right||A.clientY<ae.top||A.clientY>ae.bottom},Me=A=>K=se(A),Ie=A=>K&&se(A)&&c.close();return"closedBy"in HTMLDialogElement.prototype||(c.addEventListener("pointerdown",Me),c.addEventListener("pointerup",Ie)),()=>{c.removeEventListener("close",_),c.removeEventListener("pointerdown",Me),c.removeEventListener("pointerup",Ie)}},[]);let p=()=>o.current?.close(),d=c=>()=>x(c),u=L.value,g=u.page==="group"?u.path:".",$=(c,_,K,se)=>({section:"Commands",label:c,detail:_,sym:{icon:K,tone:"muted",label:c},run:se}),v=[...l.map(c=>({section:"Groups",label:c.path==="."?"local":c.path,detail:`${c.runs} runs${c.proposal?` \xB7 ${c.proposal}`:""}`,sym:w("research",c.status),run:d(f(c.path))})),...i.map(c=>({section:"Runs",label:c["run.name"]??c["run.id"],detail:`${c["run.status"]} \xB7 ${c["run.path"]}`,sym:w("run",c["run.status"]),run:d(f(c["run.path"]))})),$("Theme: light","","sun",()=>ce("light")),$("Theme: dark","","moon",()=>ce("dark")),$("Theme: follow the system","","monitor",()=>ce("system")),$("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),$("Show notes and timeline","i","file-text",d(f(g,{drawer:!0}))),$("Show or hide the sidebar","\u2318B","panel-left",()=>M.set(!M.value)),$(N.value?"Resume live updates":"Pause live updates","p",N.value?"play":"pause",()=>N.set(!N.value)),$("Keyboard shortcuts","?","keyboard",()=>B.set(!0)),$("Settings","","settings",d("/settings/appearance"))].map(c=>({it:c,s:Math.max(Mt(t,c.label),Mt(t,c.detail)*.5)})).filter(c=>c.s>0).sort((c,_)=>_.s-c.s||It(c.it.section)-It(_.it.section)).slice(0,60).map(c=>c.it),k=c=>{c&&(p(),c.run())},G=c=>{if(c.key==="ArrowDown")r(Math.min(v.length-1,n+1));else if(c.key==="ArrowUp")r(Math.max(0,n-1));else if(c.key==="Enter")k(v[n]);else return;c.preventDefault()},Le="";return a`<dialog class="sheet" ref=${o} aria-label="Search" closedby="any">
    <div class="palette-input"><${m} name="search" size=${18} />
      <input autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${v[n]?`pal-${n}`:void 0}
        onInput=${c=>{s(c.target.value),r(0)}} onKeyDown=${G} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${v.map((c,_)=>{let K=c.section!==Le&&!t?Le=c.section:null;return a`${K?a`<li class="section" role="presentation">${K}</li>`:null}
          <li id=${`pal-${_}`} class="item" role="option" aria-selected=${_===n}
              onMouseMove=${()=>r(_)} onClick=${()=>k(c)}>
            <${T} spec=${c.sym} /><span class="label">${c.label}</span><span class="detail">${c.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function It(e){return["Groups","Runs","Commands"].indexOf(e)}function fe(e){let t=new Map;for(let n of e)t.set(n.path,{path:n.path,name:n.path==="."?"local":n.path.split("/").pop(),runs:n.runs??0,running:n.running??0,failed:(n.failed??0)+(n.killed??0)+(n.lost??0),status:n.status??null,children:[]});let s=t.get(".")??{path:".",name:"local",runs:0,running:0,failed:0,status:null,children:[]};for(let n of t.values()){if(n.path===".")continue;let r=n.path.lastIndexOf("/");(t.get(r<0?".":n.path.slice(0,r))??s).children.push(n)}for(let n of t.values())n.children.sort((r,o)=>r.name.localeCompare(o.name));return s}function _t(e,t,s){let n=[],r=s.toLowerCase(),o=l=>{(!r||l.path.toLowerCase().includes(r)||Nt(l,r))&&(n.push(l),(r||t.has(l.path)||l.path===".")&&l.children.forEach(o))};return o(e),n}function Nt(e,t){return e.children.some(s=>s.path.toLowerCase().includes(t)||Nt(s,t))}function zt(e,t){let s=t.lastIndexOf("/"),n=t==="."?null:s<0?".":t.slice(0,s);if(n===null)return[e];let r=o=>o.path===n?o:o.children.map(r).find(l=>l)??null;return r(e)?.children??[]}function Rt(e){return e==="."?0:e.split("/").length}function Ht(){let e=b(L),t=h(q()),[s,n]=y(()=>new Set(Q("open",[]))),[r,o]=y(""),l=U(null),i=e.page==="group"?e.path:null,p=fe(E(t.data)),d=_t(p,sn(s,i),r),u=($,D)=>{let v=new Set(s);D??!v.has($)?v.add($):v.delete($),Z("open",[...v]),n(v)};return a`<nav class="sidebar" aria-label="Groups">
    <label class="filter"><${m} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${r} aria-label="Filter groups"
        onInput=${$=>o($.target.value)} />
    </label>
    <div class="tree" ref=${l} onKeyDown=${$=>{let D=[...l.current?.querySelectorAll("a.tree-item")??[]],v=D.indexOf(document.activeElement),k=d[v];switch($.key){case"ArrowDown":D[Math.min(D.length-1,v+1)]?.focus();break;case"ArrowUp":D[Math.max(0,v-1)]?.focus();break;case"ArrowRight":k?.children.length&&u(k.path,!0);break;case"ArrowLeft":k&&s.has(k.path)?u(k.path,!1):k&&D[d.findIndex(G=>G.path===nn(k.path))]?.focus();break;default:return}$.preventDefault()}} role="tree">
      ${d.map($=>a`<${tn} key=${$.path} node=${$} current=${$.path===i}
        open=${s.has($.path)||!!r} onToggle=${()=>u($.path)} />`)}
    </div>
  </nav>`}function tn(e){let t=e.node,s=()=>at(t.path),n=t.children.length>0&&t.path!==".";return a`<a class=${`tree-item${e.current?" current":""}`} href=${f(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${n?e.open:void 0}
      style=${`padding-inline-start:${6+Rt(t.path)*14}px`} onMouseEnter=${s} onFocus=${s}
      onClick=${r=>{r.metaKey||r.ctrlKey||(r.preventDefault(),x(f(t.path)))}}>
    <span class="twisty" onClick=${r=>{r.preventDefault(),r.stopPropagation(),e.onToggle()}}>
      ${n?a`<${m} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?a`<${T} spec=${w("run","running")} size=${13} />`:null}
      ${t.failed?a`<${T} spec=${{...w("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${13} />`:null}
    </span>
    <span class="count">${t.runs||""}</span>
  </a>`}function nn(e){let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function sn(e,t){if(!t||t===".")return e;let s=new Set(e),n=t.split("/");for(let r=1;r<n.length;r++)s.add(n.slice(0,r).join("/"));return s}function At(){let e=b(L),t=b(M),s=b(I),n=b(B),r=U(null);C(()=>Be(()=>r.current),[]),C(()=>(addEventListener("keydown",Bt),()=>removeEventListener("keydown",Bt)),[]);let o=e.page==="group"&&e.drawer,l;switch(e.page){case"group":l=a`<${Ct} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":l=a`<${Lt} id=${e.id} />`;break;case"settings":l=a`<${gt} />`;break;case"timeline":l=a`<${ot} key=${e.from} from=${e.from} />`;break;default:l=a`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return te?a`<main class="main render-main" ref=${r}>${l}</main>`:a`<div class=${`shell${t?"":" no-sidebar"}${o?" with-drawer":""}`}>
    <${bt} />
    ${t?a`<${Ht} />`:null}
    <main class="main" ref=${r}>${l}</main>
    ${o?a`<${wt} path=${e.path} run=${e.run} />`:null}
    <${yt} />
    ${s!==null?a`<${Dt} query=${s} />`:null}
    ${n?a`<${rn} />`:null}
  </div>`}function Bt(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),I.set(I.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),M.set(!M.value);return}if(e.key==="Escape"){if(I.value!==null||B.value)return;let n=L.value;return n.page==="group"&&n.run?x(f(n.path,{drawer:!0}),{replace:!0}):n.page==="group"&&n.drawer?x(f(n.path),{replace:!0}):void 0}if(t||e.altKey||ft(e)||I.value!==null||B.value)return;let s=L.value;switch(e.key){case"/":e.preventDefault(),I.set("");break;case"?":B.set(!B.value);break;case"p":N.set(!N.value);break;case"i":s.page==="group"&&x(f(s.path,{drawer:!s.drawer}),{replace:!0});break;case"b":M.set(!M.value);break;case"[":case"]":s.page==="group"&&an(s.path,e.key==="]"?1:-1);break}}async function an(e,t){let s=fe(E(await oe(q()))),n=zt(s,e),r=n.findIndex(l=>l.path===e),o=n[r+t];o&&x(f(o.path))}function rn(){let e=U(null);return C(()=>{let t=e.current;t.showModal();let s=()=>B.set(!1);return t.addEventListener("close",s),()=>t.removeEventListener("close",s)},[]),a`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${he.map(([t,s])=>a`<tr><td><kbd>${t}</kbd></td><td>${s}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 14px"><button class="link" autofocus>Close</button></form>
    </div>
  </dialog>`}var S=null,X=null,ge,ne;function Kt(){S=document.createElement("div"),S.className="bt-hint",S.setAttribute("popover","manual"),S.id="bt-hint",document.body.append(S),S.addEventListener("pointerenter",()=>clearTimeout(ne)),S.addEventListener("pointerleave",()=>Pt()),document.addEventListener("pointerover",e=>{let t=e.target.closest?.("[data-tip]");t&&t!==X&&(clearTimeout(ge),ge=setTimeout(()=>Ot(t),X?0:350))}),document.addEventListener("pointerout",e=>{let t=e.target.closest?.("[data-tip]");t&&(clearTimeout(ge),t===X&&Pt())}),document.addEventListener("focusin",e=>{let t=e.target.closest?.("[data-tip]");t&&e.target.matches(":focus-visible")&&Ot(t)}),document.addEventListener("focusout",()=>ve()),document.addEventListener("keydown",e=>{e.key==="Escape"&&X&&ve()}),document.addEventListener("pointerdown",()=>ve(),!0)}function Ot(e){let t=e.getAttribute("data-tip");if(!S||!t||!e.isConnected)return;clearTimeout(ne),X=e,S.textContent=t,S.matches(":popover-open")||S.showPopover();let s=e.getBoundingClientRect(),n=S.getBoundingClientRect(),r=6,o=s.top-n.height-r,l=o>=4?o:s.bottom+r,i=Math.min(Math.max(4,s.left+s.width/2-n.width/2),innerWidth-n.width-4);S.style.top=`${l}px`,S.style.left=`${i}px`}function Pt(){clearTimeout(ne),ne=setTimeout(ve,120)}function ve(){clearTimeout(ge),clearTimeout(ne),X=null,S?.matches(":popover-open")&&S.hidePopover()}Oe();if(te){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(R.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>_e.n}else Re();Kt();re("meta").then(e=>{te&&(e={...e,settings:{...e.settings,theme_mode:R.value}}),xe(e)});De(a`<${At} />`,document.getElementById("app"));
