import{$ as de,A as ye,Aa as me,B as f,Ba as rt,C as ne,Ca as ot,D as L,Da as it,E as Ae,Ea as lt,Fa as ke,G as x,Ga as w,H as Be,Ha as xe,I as Pe,Ia as ct,J as G,Ja as dt,K as P,Ka as ut,L as ie,M as le,N,Na as pt,Oa as mt,Pa as ht,Qa as $t,U as Oe,V as R,X as we,Y as ce,Z as Ke,_ as q,aa as m,ba as T,c as De,ca as H,d as a,da as E,e as y,ea as O,f as C,fa as Ue,g as U,ga as je,h as J,ha as Fe,ia as Ve,ja as Ge,k as Q,ka as qe,l as b,la as We,m as Z,ma as Xe,n as ee,na as Ye,oa as W,pa as j,q as te,qa as Je,r as _e,ra as Qe,s as oe,sa as Ze,t as h,ta as et,ua as ue,v as z,va as tt,w as ze,wa as pe,x as Ne,xa as nt,y as Re,ya as st,z as He,za as at}from"./chunks/chunk-B7TSUZO6.js";import"./chunks/chunk-EBVYA7LM.js";import"./chunks/chunk-VC46IEJQ.js";var M=new Q(Z("sidebar",!0)),I=new Q(null),A=new Q(!1),X=new Q(null);M.subscribe(e=>ee("sidebar",e));var ft=Z("visit",Date.now());ee("visit",Date.now());function gt(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var he=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var jt=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function $e(e){X.set(e),Oe.set(e.theme),e.settings?.theme_mode&&R.set(e.settings.theme_mode),we()}async function Te(e,t){e==="theme_mode"&&(R.set(t),we()),$e(await Xe(e,t))}function vt(){let e=b(R),t=q(),s=b(X),[n,o]=y(null);C(()=>{document.title="Settings \xB7 Beamtime"},[]);let r=(i,p)=>{o(null),Te(i,p).catch(d=>o(d.message))},l=s?.settings??{};return a`<div class="page settings">
    <header class="header"><h1 class="title" tabindex="-1">Settings</h1></header>
    <p class="muted small">Changes are written to <code>${l.file??"beamtime.yaml"}</code>, the project's settings.</p>
    ${n?a`<${H} kind="error">${n}<//>`:null}
    <h2>Appearance</h2>
    <div class="settings-rows">
      <span class="field-label">Mode</span>
      <div class="segmented" role="radiogroup" aria-label="Theme mode">
        ${jt.map(([i,p,d])=>a`<button type="button" role="radio" aria-checked=${e===i} onClick=${()=>r("theme_mode",i)}>
          <${m} name=${p} size=${15} />${d}</button>`)}
      </div>
      <span class="field-label">Theme</span>
      <select value=${l.theme} onChange=${i=>r("theme",i.target.value)}>
        ${(s?.themes??[]).map(i=>a`<option value=${i}>${i}</option>`)}
      </select>
    </div>
    <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files go in <code>themes/</code> next to beamtime.yaml.</p>
    ${(s?.theme?.problems??[]).map(i=>a`<${H} kind="warning">${i}<//>`)}
    <h2>Figures</h2>
    <div class="settings-rows">
      <span class="field-label">Style sheets</span>
      ${(s?.figure_styles??[]).length?a`<${Ye} options=${s.figure_styles} value=${l.figure_style??[]} label="Style sheets"
            placeholder="Add a style" onChange=${i=>r("figure_style",i)} />`:a`<span class="muted small"><code>${JSON.stringify(l.figure_style??[])}</code>; choosing others needs the figures
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
  </div>`}var bt={system:"light",light:"dark",dark:"system"},Ft={system:"monitor",light:"sun",dark:"moon"};function yt(){let e=b(X),t=b(R),s=b(M);return a`<header class="topbar">
    <${O} icon="panel-left" label=${s?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${s} onClick=${()=>M.set(!s)} />
    <a class="project" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search" onClick=${()=>I.set("")} aria-label="Search (⌘K)">
      <${m} name="search" size=${15} /><span class="search-label">Search groups, runs, commands</span><kbd>⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <span class="source" data-tip="Sources: this machine. Remote sources come later."><${m} name="server" size=${15} /> local</span>
      <${O} icon=${Ft[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${bt[t]})`}
        onClick=${()=>{Te("theme_mode",bt[t])}} />
      <a class="icon-button" href=${lt(L.value.page==="group"?L.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${m} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${m} name="settings" size=${16} /></a>
    </div>
  </header>`}function Vt(e){let[t,s]=y(Date.now());return C(()=>{let n=setInterval(()=>s(Date.now()),e);return()=>clearInterval(n)},[e]),t}function Gt(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function wt(){let e=b(ze),t=b(z),s=b(Ne),n=b(L),o=Vt(5e3),r=h(at()).data,l=E(h(me()).data),i=b(X),p=r?.daemon,d=r?.runs?.running??0,u=l.filter(k=>k["run.status"]==="failed"&&Gt(k["run.ended_at"])>ft).length,g=r?.meta?.freshness,[$,D,v]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&p?["",`live \xB7 updated ${N(new Date(s).toISOString(),o)}`,`beamtime serve, pid ${p.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return a`<footer class="statusbar">
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
    <${O} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>z.set(!t)} />
    ${i?.outdated?a`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item subtle">${i?.version?`beamtime ${i.version}`:""}</span>
  </footer>`}function kt(e){let t=()=>x(f(e.path),{replace:!0});return a`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head">
      <span class="status-item"><${m} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${O} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?a`<${qt} id=${e.run} scope=${e.path} />`:a`<${Wt} path=${e.path} />`}
  </aside>`}function qt({id:e,scope:t}){let s=h(ue(e,t)).data,n=h(tt(e,t)).data,o=h(pe(t)).data,r=q(),l=J(()=>de(E(o).map(d=>d["run.id"]),r).get(e),[o,r,e]);if(!s)return a`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let i=s.run,p=Object.entries(s.metrics??{});return a`<div class="drawer-body">
    <h3><span class="run-dot" style=${`background:${l??"var(--bt-subtle)"}`}></span>
      <a href=${ne(e)}>${i.name}</a></h3>
    <p class="facts small">
      <${T} spec=${w("run",i.status)} word />
      <span class="fact"><b>${ie(i.steps)}</b> steps</span>
      <span class="fact"><b>${le(i.duration_s)}</b></span>
      <span class="fact" data-tip=${i.created_at}>${N(i.created_at)}</span>
    </p>
    ${i.error?a`<pre class="log bad-text">${i.error}</pre>`:null}
    <h4>Config</h4>
    <table class="kv">${Object.entries(s.config??{}).map(([d,u])=>a`<tr><td>${d}</td><td class="num">${P(u)}</td></tr>`)}</table>
    ${p.length?a`<h4>Metrics</h4>
          <table class="kv">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${p.map(([d,u])=>a`<tr><td>${d}</td><td class="num"><b>${P(u.last)}</b></td>
              <td class="num">${P(u.min)}</td><td class="num">${P(u.max)}</td></tr>`)}
          </table>`:null}
    ${s.cited_by?.length?a`<h4>Cited by</h4>${s.cited_by.map(d=>a`<p class="small"><${T} spec=${w("note",d.type)} /> ${d.description}</p>`)}`:null}
    <h4>Events</h4>
    ${(s.events??[]).slice(-8).map(d=>a`<div class="event"><span class="muted num">${d.t?.slice(5,16).replace("T"," ")}</span>
        <${m} name=${xe(d.type)} size=${14} /><span>${d.description}</span></div>`)}
    <h4>Output</h4>
    <pre class="log">${(n?.lines??[]).join(`
`)}</pre>
  </div>`}function Wt({path:e}){let t=h(nt(e)).data,s=h(st(e)).data;return a`<div class="drawer-body">
    <h4 style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?a`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(n=>!String(n.state??"").startsWith("superseded")).map(n=>a`<${ut} key=${n.id} note=${n} />`)}</div>
    <h4>Timeline</h4>
    ${(s?.entries??[]).slice().reverse().map(n=>a`<div class="event"><span class="muted num">${n.t?.slice(5,16).replace("T"," ")}</span>
        <${m} name=${n.kind==="note"?"file-text":xe(n.type)} size=${14} />
        <span>${n.run?a`<a href=${ne(n.run)}>${n.run.slice(-8)}</a> `:null}${n.description??n.type}</span></div>`)}
  </div>`}var Se=["failed","killed","lost"];function Ee(e){let t=e.path==="."?[]:e.path.split("/"),s=t.length&&ye(t[t.length-1])?t[t.length-1]:null,n=t.slice(0,-1);return a`<header class="header">
    <nav class="crumbs" aria-label="Breadcrumb">
      ${t.length?a`<a href=${f(".")}>local</a>`:null}
      ${n.map((o,r)=>a`<span class="sep">/</span><a href=${f(n.slice(0,r+1).join("/"))}>${o}</a>`)}
    </nav>
    ${s?a`<${Yt} id=${s} scope=${e.path} />`:a`<${Xt} path=${e.path} />`}
    ${e.finding?a`<p class="finding">${e.finding}</p>`:null}
  </header>`}function Xt({path:e}){let t=E(h(Qe(e)).data)[0]??null,s=h(t?.proposal?Ze(e):null).data,n=h(t?.proposal?et(e):null).data,o=n?.proposal?.rationale,r=n?.versions?.find(u=>u.version===n.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,l=e==="."?"local":e.split("/").pop();if(!t)return a`<h1 class="title" tabindex="-1">${l}</h1><div class="skeleton late" style="block-size: 52px"></div>`;let[i,p]=dt(s?.progress?.text??t.progress),d=Se.reduce((u,g)=>u+(t[g]??0),0);return a`
    <h1 class="title" tabindex="-1">${l} <${T} spec=${w("research",t.status)} word /></h1>
    ${t.proposal?a`<div class="statement">
          <${ke} value=${t.proposal} label="the proposal's statement" locked=${n?r:"Loading the proposal\u2026"}
            render=${u=>a`<span data-tip=${r?void 0:o}>${u}</span>`}
            onSave=${u=>Fe(e,u)} />
        </div>`:null}
    ${t.proposal?a`<div class="preds">
          ${(s?.predictions??[]).map(u=>a`<span class="pred" key=${u.name} data-tip=${ct(u)}>
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
      <${xt} path=${e} />
    </div>`}function Yt({id:e,scope:t}){let s=h(ue(e,t)).data;if(!s)return a`<h1 class="title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 52px"></div>`;let n=s.run,o=()=>{navigator.clipboard?.writeText(n.id)};return a`
    <h1 class="title" tabindex="-1"><${ke} value=${n.name??n.id} label="the run's name" class="title-edit"
        onSave=${r=>Ve(n.id,t,r.trim())} />
      <${T} spec=${w("run",n.status)} word /></h1>
    ${n.error?a`<p class="statement bad-text" data-tip=${n.error}>${n.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span class="fact"><b>${ie(n.steps)}</b> steps</span>
      <span class="fact"><b>${le(n.duration_s)}</b></span>
      <span class="fact" data-tip=${n.created_at}>${N(n.created_at)}</span>
      <${xt} path=${t} />
      <span class="fact">
        <${O} icon="copy" label=${`Copy the run id ${n.id}`} onClick=${o} />
        <${je} icon="ellipsis" label="Details" title="Run details" class="run-details">
          <table class="kv">${Jt(n).map(([r,l])=>a`<tr><td class="muted">${r}</td><td>${l}</td></tr>`)}</table>
          <div class="menu-list">
            <button type="button" onClick=${()=>x(f(t,{run:n.id}),{replace:!0})}>
              <${m} name="panel-right" size=${15} /> Open in the side panel</button>
            <button type="button" onClick=${o}><${m} name="copy" size=${15} /> Copy the run id</button>
            ${n.git?.commit?a`<button type="button" onClick=${()=>navigator.clipboard?.writeText(n.git.commit)}>
              <${m} name="git-commit" size=${15} /> Copy the commit</button>`:null}
          </div>
        <//>
      </span>
    </div>
    ${(s.proposals??[]).length?a`<div class="preds" style="margin-block-start: 10px">
          ${s.proposals.map(r=>a`<a class="pred" href=${f(r.group)} data-tip=${r.statement}>
              <${T} spec=${w("result",r.check)} /><b>${r.group==="."?"own proposal":r.group}</b>
              ${r.verdict?a`<${T} spec=${w("verdict",r.verdict)} />`:null}</a>`)}
        </div>`:null}`}function xt({path:e}){let t=h(Je(e)).data?.summary;if(!t)return null;let s=Object.entries(t.config??{}).map(([o,r])=>`${o} ${P(r)}`).join(", "),n=ye(e.split("/").pop()??"");return a`<span class="fact" data-tip=${`${t.stat} of ${t.metric} over ${n?"the run":"all runs"}`}>
    best <b>${t.metric} ${P(t.value)}</b>
    ${n?null:a`<span>· <a href=${ne(t.run)}>${t.name}</a>${s?a` <em>(${s})</em>`:null}</span>`}
  </span>`}function Jt(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(s=>!!s[1]).map(([s,n])=>[s,String(n)])}function Tt(e,t){let s=e.split(`
`),n=t.split(`
`),o=s.length,r=n.length,l=Array.from({length:o+1},()=>new Uint32Array(r+1));for(let u=o-1;u>=0;u--)for(let g=r-1;g>=0;g--)l[u][g]=s[u]===n[g]?l[u+1][g+1]+1:Math.max(l[u+1][g],l[u][g+1]);let i=[],p=0,d=0;for(;p<o&&d<r;)s[p]===n[d]?(i.push({kind:"same",text:s[p]}),p++,d++):l[p+1][d]>=l[p][d+1]?i.push({kind:"removed",text:s[p++]}):i.push({kind:"added",text:n[d++]});for(;p<o;)i.push({kind:"removed",text:s[p++]});for(;d<r;)i.push({kind:"added",text:n[d++]});return i}function St(e,t=3){let s=[],n=0;for(;n<e.length;){if(e[n].kind!=="same"){s.push(e[n++]);continue}let o=n;for(;o<e.length&&e[o].kind==="same";)o++;let r=n===0?0:t,l=o===e.length?0:t;o-n>r+l+1?s.push(...e.slice(n,n+r),{kind:"skip",count:o-n-r-l},...e.slice(o-l,o)):s.push(...e.slice(n,o)),n=o}return s}function fe(e){let t=h(pe(e.path)),s=q(),n=E(t.data),o=J(()=>de(n.map(i=>i["run.id"]),s),[t.data,s]),r=J(()=>new Map(n.map(i=>[i["run.id"],i["run.name"]??i["run.id"]])),[t.data]);if(!e.view)return a`<div class="view"><div class="skeleton late" style="block-size: 320px"></div></div>`;let l={path:e.path,colors:o,names:r,metrics:e.view.metrics??{}};return a`<div class="view"><${Ke.Provider} value=${l}><${$t} node=${e.view.view} /><//></div>`}function Et(e){let t=e.view,s=b(L),n=s.page==="group"&&s.version,o=t.versions?a`<a href=${f(e.path,{history:!0})}><${m} name="history" size=${14} /> history (${t.versions})</a>`:null,r;switch(t.source){case"draft":r=a`draft <b>${t.draft}</b>`;break;case"view":r=a`${t.title?a`<em>${t.title}</em> · `:null}saved ${N(Ce(t.version))} by ${t.author??"unknown"}`;break;default:r=a`the built-in view`}return a`<div class="view-source">
    <${m} name="layout" size=${14} /><span>${r}</span>
    ${n?a`<a href=${f(e.path)}>an older version · show the current one</a>`:null}
    ${o}
    ${t.outdated?.length&&!n?a`<${Qt} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||n?null:a`<${Zt} path=${e.path} />
        <${en} path=${e.path} view=${t} />`}
  </div>`}function Qt(e){let[t,s]=y(null),n=e.outdated.map(r=>r.name).join(", ");return a`<button type="button" class="link small" onClick=${async()=>{s(null);try{await qe(e.path)}catch(r){s(r.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${n} exists; update re-pins this view to it (a new version)`}>
      <${m} name="update" size=${14} /> update ${n}</button>
    ${t?a`<span class="bad-text small">${t}</span>`:null}`}function Zt(e){let[t,s]=y(null);return a`<button type="button" class="link small" onClick=${async()=>{s(null);try{We.set(await Ge(e.path,null,""))}catch(o){s(o.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${m} name="file-text" size=${14} /> add text</button>
    ${t?a`<span class="bad-text small">${t}</span>`:null}`}function en(e){let t=pt(e.path),s=ht(t),[n,o]=y(!1),[r,l]=y(e.view.title??""),[i,p]=y(e.view.finding??""),[d,u]=y(null),[g,$]=y(!1);if(!s&&!n)return null;let D=async v=>{v.preventDefault(),$(!0),u(null);try{let k={charts:t.charts,added:t.added,order:t.order,spans:t.spans};await te("save_view",{path:e.path,prefs:k,title:r,finding:i}),mt(e.path,()=>({view:{},charts:{},added:[],order:{},spans:{}})),He(V=>["view","view_history","summary"].includes(V.method)&&V.scope===e.path),o(!1)}catch(k){u(k.message)}finally{$(!1)}};return n?a`<form class="save-form" onSubmit=${D}>
    <label class="field"><span class="field-label">Title</span>
      <input value=${r} onInput=${v=>l(v.target.value)} /></label>
    <label class="field"><span class="field-label">Finding</span>
      <input value=${i} placeholder="the key result in one sentence"
        onInput=${v=>p(v.target.value)} /></label>
    <div class="save-actions">
      <button type="submit" class="button primary" disabled=${g}>${g?"Saving\u2026":"Save as view"}</button>
      <button type="button" class="link small" onClick=${()=>o(!1)}>cancel</button>
      ${d?a`<span class="bad-text small">${d}</span>`:null}
    </div>
  </form>`:a`<button type="button" class="link small save-view" onClick=${()=>o(!0)}
        data-tip="Save your chart settings and added charts as this page's view, for everyone">
      <${m} name="save" size=${14} /> Save as view</button>`}function Ct(e){let t=h(ot(e.path)),s=t.data?.entries??[],[n,o]=y(null),r=n??s.slice(0,2).map(i=>i.version).reverse(),l=i=>{let p=r.includes(i)?r.filter(d=>d!==i):[...r,i].slice(-2);o(p.sort())};return t.status==="error"?a`<${H} kind="error">${t.error}<//>`:a`<section class="history">
    <h2 class="history-title"><${m} name="history" size=${18} /> View history</h2>
    ${t.data&&!s.length?a`<${H}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${s.map((i,p)=>a`<li key=${i.version} class=${r.includes(i.version)?"picked":""}>
          <label><input type="checkbox" checked=${r.includes(i.version)} onChange=${()=>l(i.version)} />
            <span class="num muted" data-tip=${i.version}>${N(i.time)}</span>
            <b>${i.title??"untitled"}</b><span class="muted">${i.author??""}</span>
            ${i.message?a`<span>${i.message}</span>`:null}</label>
          <a href=${p===0?f(e.path):f(e.path,{version:i.version})}
            onClick=${d=>{d.preventDefault(),x(p===0?f(e.path):f(e.path,{version:i.version}))}}>${p===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${r.length===2?a`<${tn} path=${e.path} a=${r[0]} b=${r[1]} />`:null}
  </section>`}function tn(e){let t=i=>({method:"view_show",params:{group:e.path,version:i},scope:e.path}),s=h(t(e.a)).data,n=h(t(e.b)).data,o=h(j(e.path,e.a)).data,r=h(j(e.path,e.b)).data,l=s&&n?St(Tt(s.yaml,n.yaml)):[];return a`<div class="compare">
    <h3 class="block-title">Changes from ${N(Ce(e.a))} to ${N(Ce(e.b))}</h3>
    <pre class="diff">${l.map(i=>i.kind==="skip"?a`<div class="diff-skip">⋯ ${i.count} unchanged lines</div>`:a`<div class=${`diff-${i.kind}`}>${i.kind==="added"?"+ ":i.kind==="removed"?"\u2212 ":"  "}${i.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title">${o?.title??e.a}</h3><${fe} path=${e.path} view=${o} /></div>
      <div><h3 class="block-title">${r?.title??e.b}</h3><${fe} path=${e.path} view=${r} /></div>
    </div>
  </div>`}function Ce(e){return e?`${e.slice(0,4)}-${e.slice(4,6)}-${e.slice(6,8)}T${e.slice(9,11)}:${e.slice(11,13)}:${e.slice(13,15)}Z`:null}function Lt(e){return C(()=>{document.title=`${e.path==="."?"local":e.path} \xB7 Beamtime`},[e.path]),e.history?a`<div class="page"><${Ee} path=${e.path} /><${Ct} path=${e.path} /></div>`:a`<div class="page">
    <${nn} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function nn(e){let t=h(j(e.path,e.version,e.draft));return C(()=>{t.status==="ready"&&requestAnimationFrame(Be)},[t.status==="ready"]),a`
    <${Ee} path=${e.path} finding=${t.data?.finding} />
    ${t.data?a`<${Et} path=${e.path} view=${t.data} />`:null}
    ${t.status==="error"?a`<${H} kind="error">${t.error}<//>`:a`<${fe} path=${e.path} view=${t.data} />`}`}function Mt(e){C(()=>{oe(j(e.id)).then(s=>x(f(s.path),{replace:!0})).catch(()=>{})},[e.id]);let t=h(j(e.id));return t.status==="error"?a`<div class="page"><${H} kind="error">${t.error}<//></div>`:a`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}function It(e,t){let s=e.toLowerCase(),n=t.toLowerCase();if(!s)return 1;let o=n.indexOf(s);if(o>=0)return 100-Math.min(o,50)-n.length/100;let r=0,l=0;for(let i of n)if(i===s[r]?r++:r>0&&l++,r===s.length)return 40-Math.min(l,39);return 0}function _t(e){let[t,s]=y(e.query),[n,o]=y(0),r=U(null),l=E(h(W()).data),i=E(h(me()).data);C(()=>{let c=r.current;c.showModal();let _=()=>I.set(null);c.addEventListener("close",_);let K=!1,ae=B=>{let re=c.getBoundingClientRect();return B.clientX<re.left||B.clientX>re.right||B.clientY<re.top||B.clientY>re.bottom},Me=B=>K=ae(B),Ie=B=>K&&ae(B)&&c.close();return"closedBy"in HTMLDialogElement.prototype||(c.addEventListener("pointerdown",Me),c.addEventListener("pointerup",Ie)),()=>{c.removeEventListener("close",_),c.removeEventListener("pointerdown",Me),c.removeEventListener("pointerup",Ie)}},[]);let p=()=>r.current?.close(),d=c=>()=>x(c),u=L.value,g=u.page==="group"?u.path:".",$=(c,_,K,ae)=>({section:"Commands",label:c,detail:_,sym:{icon:K,tone:"muted",label:c},run:ae}),v=[...l.map(c=>({section:"Groups",label:c.path==="."?"local":c.path,detail:`${c.runs} runs${c.proposal?` \xB7 ${c.proposal}`:""}`,sym:w("research",c.status),run:d(f(c.path))})),...i.map(c=>({section:"Runs",label:c["run.name"]??c["run.id"],detail:`${c["run.status"]} \xB7 ${c["run.path"]}`,sym:w("run",c["run.status"]),run:d(f(c["run.path"]))})),$("Theme: light","","sun",()=>ce("light")),$("Theme: dark","","moon",()=>ce("dark")),$("Theme: follow the system","","monitor",()=>ce("system")),$("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),$("Show notes and timeline","i","file-text",d(f(g,{drawer:!0}))),$("Show or hide the sidebar","\u2318B","panel-left",()=>M.set(!M.value)),$(z.value?"Resume live updates":"Pause live updates","p",z.value?"play":"pause",()=>z.set(!z.value)),$("Keyboard shortcuts","?","keyboard",()=>A.set(!0)),$("Settings","","settings",d("/settings/appearance"))].map(c=>({it:c,s:Math.max(It(t,c.label),It(t,c.detail)*.5)})).filter(c=>c.s>0).sort((c,_)=>_.s-c.s||Dt(c.it.section)-Dt(_.it.section)).slice(0,60).map(c=>c.it),k=c=>{c&&(p(),c.run())},V=c=>{if(c.key==="ArrowDown")o(Math.min(v.length-1,n+1));else if(c.key==="ArrowUp")o(Math.max(0,n-1));else if(c.key==="Enter")k(v[n]);else return;c.preventDefault()},Le="";return a`<dialog class="sheet" ref=${r} aria-label="Search" closedby="any">
    <div class="palette-input"><${m} name="search" size=${18} />
      <input autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${v[n]?`pal-${n}`:void 0}
        onInput=${c=>{s(c.target.value),o(0)}} onKeyDown=${V} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${v.map((c,_)=>{let K=c.section!==Le&&!t?Le=c.section:null;return a`${K?a`<li class="section" role="presentation">${K}</li>`:null}
          <li id=${`pal-${_}`} class="item" role="option" aria-selected=${_===n}
              onMouseMove=${()=>o(_)} onClick=${()=>k(c)}>
            <${T} spec=${c.sym} /><span class="label">${c.label}</span><span class="detail">${c.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function Dt(e){return["Groups","Runs","Commands"].indexOf(e)}function ge(e){let t=new Map;for(let n of e)t.set(n.path,{path:n.path,name:n.path==="."?"local":n.path.split("/").pop(),runs:n.runs??0,running:n.running??0,failed:(n.failed??0)+(n.killed??0)+(n.lost??0),status:n.status??null,children:[]});let s=t.get(".")??{path:".",name:"local",runs:0,running:0,failed:0,status:null,children:[]};for(let n of t.values()){if(n.path===".")continue;let o=n.path.lastIndexOf("/");(t.get(o<0?".":n.path.slice(0,o))??s).children.push(n)}for(let n of t.values())n.children.sort((o,r)=>o.name.localeCompare(r.name));return s}function zt(e,t,s){let n=[],o=s.toLowerCase(),r=l=>{(!o||l.path.toLowerCase().includes(o)||Nt(l,o))&&(n.push(l),(o||t.has(l.path)||l.path===".")&&l.children.forEach(r))};return r(e),n}function Nt(e,t){return e.children.some(s=>s.path.toLowerCase().includes(t)||Nt(s,t))}function Rt(e,t){let s=t.lastIndexOf("/"),n=t==="."?null:s<0?".":t.slice(0,s);if(n===null)return[e];let o=r=>r.path===n?r:r.children.map(o).find(l=>l)??null;return o(e)?.children??[]}function Ht(e){return e==="."?0:e.split("/").length}function At(){let e=b(L),t=h(W()),[s,n]=y(()=>new Set(Z("open",[]))),[o,r]=y(""),l=U(null),i=e.page==="group"?e.path:null,p=ge(E(t.data)),d=zt(p,rn(s,i),o),u=($,D)=>{let v=new Set(s);D??!v.has($)?v.add($):v.delete($),ee("open",[...v]),n(v)};return a`<nav class="sidebar" aria-label="Groups">
    <label class="filter"><${m} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${o} aria-label="Filter groups"
        onInput=${$=>r($.target.value)} />
    </label>
    <div class="tree" ref=${l} onKeyDown=${$=>{let D=[...l.current?.querySelectorAll("a.tree-item")??[]],v=D.indexOf(document.activeElement),k=d[v];switch($.key){case"ArrowDown":D[Math.min(D.length-1,v+1)]?.focus();break;case"ArrowUp":D[Math.max(0,v-1)]?.focus();break;case"ArrowRight":k?.children.length&&u(k.path,!0);break;case"ArrowLeft":k&&s.has(k.path)?u(k.path,!1):k&&D[d.findIndex(V=>V.path===an(k.path))]?.focus();break;default:return}$.preventDefault()}} role="tree">
      ${d.map($=>a`<${sn} key=${$.path} node=${$} current=${$.path===i}
        open=${s.has($.path)||!!o} onToggle=${()=>u($.path)} />`)}
    </div>
  </nav>`}function sn(e){let t=e.node,s=()=>rt(t.path),n=t.children.length>0&&t.path!==".";return a`<a class=${`tree-item${e.current?" current":""}`} href=${f(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${n?e.open:void 0}
      style=${`padding-inline-start:${6+Ht(t.path)*14}px`} onMouseEnter=${s} onFocus=${s}
      onClick=${o=>{o.metaKey||o.ctrlKey||(o.preventDefault(),x(f(t.path)))}}>
    <span class="twisty" onClick=${o=>{o.preventDefault(),o.stopPropagation(),e.onToggle()}}>
      ${n?a`<${m} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?a`<${T} spec=${w("run","running")} size=${13} />`:null}
      ${t.failed?a`<${T} spec=${{...w("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${13} />`:null}
    </span>
    <span class="count">${t.runs||""}</span>
  </a>`}function an(e){let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function rn(e,t){if(!t||t===".")return e;let s=new Set(e),n=t.split("/");for(let o=1;o<n.length;o++)s.add(n.slice(0,o).join("/"));return s}function Pt(){let e=b(L),t=b(M),s=b(I),n=b(A),o=U(null);C(()=>Ae(()=>o.current),[]),C(()=>(addEventListener("keydown",Bt),()=>removeEventListener("keydown",Bt)),[]);let r=e.page==="group"&&e.drawer,l;switch(e.page){case"group":l=a`<${Lt} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":l=a`<${Mt} id=${e.id} />`;break;case"settings":l=a`<${vt} />`;break;case"timeline":l=a`<${it} key=${e.from} from=${e.from} />`;break;default:l=a`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return G?a`<main class="main render-main" ref=${o}>${l}</main>`:a`<div class=${`shell${t?"":" no-sidebar"}${r?" with-drawer":""}`}>
    <${yt} />
    ${t?a`<${At} />`:null}
    <main class="main" ref=${o}>${l}</main>
    ${r?a`<${kt} path=${e.path} run=${e.run} />`:null}
    <${wt} />
    ${s!==null?a`<${_t} query=${s} />`:null}
    ${n?a`<${ln} />`:null}
  </div>`}function Bt(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),I.set(I.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),M.set(!M.value);return}if(e.key==="Escape"){if(I.value!==null||A.value)return;let n=L.value;return n.page==="group"&&n.run?x(f(n.path,{drawer:!0}),{replace:!0}):n.page==="group"&&n.drawer?x(f(n.path),{replace:!0}):void 0}if(t||e.altKey||gt(e)||I.value!==null||A.value)return;let s=L.value;switch(e.key){case"/":e.preventDefault(),I.set("");break;case"?":A.set(!A.value);break;case"p":z.set(!z.value);break;case"i":s.page==="group"&&x(f(s.path,{drawer:!s.drawer}),{replace:!0});break;case"b":M.set(!M.value);break;case"[":case"]":s.page==="group"&&on(s.path,e.key==="]"?1:-1);break}}async function on(e,t){let s=ge(E(await oe(W()))),n=Rt(s,e),o=n.findIndex(l=>l.path===e),r=n[o+t];r&&x(f(r.path))}function ln(){let e=U(null);return C(()=>{let t=e.current;t.showModal();let s=()=>A.set(!1);return t.addEventListener("close",s),()=>t.removeEventListener("close",s)},[]),a`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${he.map(([t,s])=>a`<tr><td><kbd>${t}</kbd></td><td>${s}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 14px"><button class="link" autofocus>Close</button></form>
    </div>
  </dialog>`}var S=null,Y=null,ve,se;function Ut(){S=document.createElement("div"),S.className="bt-hint",S.setAttribute("popover","manual"),S.id="bt-hint",document.body.append(S),S.addEventListener("pointerenter",()=>clearTimeout(se)),S.addEventListener("pointerleave",()=>Kt()),document.addEventListener("pointerover",e=>{let t=e.target.closest?.("[data-tip]");t&&t!==Y&&(clearTimeout(ve),ve=setTimeout(()=>Ot(t),Y?0:350))}),document.addEventListener("pointerout",e=>{let t=e.target.closest?.("[data-tip]");t&&(clearTimeout(ve),t===Y&&Kt())}),document.addEventListener("focusin",e=>{let t=e.target.closest?.("[data-tip]");t&&e.target.matches(":focus-visible")&&Ot(t)}),document.addEventListener("focusout",()=>be()),document.addEventListener("keydown",e=>{e.key==="Escape"&&Y&&be()}),document.addEventListener("pointerdown",()=>be(),!0)}function Ot(e){let t=e.getAttribute("data-tip");if(!S||!t||!e.isConnected)return;clearTimeout(se),Y=e,S.textContent=t,S.matches(":popover-open")||S.showPopover();let s=e.getBoundingClientRect(),n=S.getBoundingClientRect(),o=6,r=s.top-n.height-o,l=r>=4?r:s.bottom+o,i=Math.min(Math.max(4,s.left+s.width/2-n.width/2),innerWidth-n.width-4);S.style.top=`${l}px`,S.style.left=`${i}px`}function Kt(){clearTimeout(se),se=setTimeout(be,120)}function be(){clearTimeout(ve),clearTimeout(se),Y=null,S?.matches(":popover-open")&&S.hidePopover()}Pe();if(G){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(R.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>_e.n}Ut();var cn=te("meta").then(e=>(G&&(e={...e,settings:{...e.settings,theme_mode:R.value}}),$e(e),e));G||Re(async()=>{let[e,t]=await Promise.all([cn,te("meta")]);e.bundle!==t.bundle?location.reload():$e(t)});De(a`<${Pt} />`,document.getElementById("app"));
