import{$ as Ke,A as ke,Aa as rt,B as $,Ba as ot,C as se,Ca as $e,D as le,Da as it,E as R,Ea as lt,F as L,Fa as ct,G as Be,Ga as dt,Ha as Se,I as S,Ia as k,J as Pe,Ja as Te,K as Ue,Ka as ut,L as W,La as pt,M as P,Ma as mt,N as ce,O as de,P as _,Pa as ht,Qa as $t,Ra as ft,Sa as gt,W as je,X as O,Z as xe,_ as ue,aa as X,ba as pe,c as ze,ca as m,d as a,da as w,e as y,ea as H,f as C,fa as E,g as F,ga as U,h as Q,ha as Fe,ia as Ve,ja as Ge,k as Z,ka as qe,l as b,la as We,m as ee,ma as Xe,n as te,na as Ye,oa as Je,pa as Qe,q as ne,qa as j,r as Ne,ra as V,s as ie,sa as Ze,t as h,ta as et,ua as tt,v as N,va as nt,w as _e,wa as me,x as He,xa as st,y as Oe,ya as he,z as Ae,za as at}from"./chunks/chunk-KRWX5B2V.js";import"./chunks/chunk-EBVYA7LM.js";import"./chunks/chunk-VC46IEJQ.js";var M=new Z(ee("sidebar",!0)),I=new Z(null),A=new Z(!1),Y=new Z(null);M.subscribe(e=>te("sidebar",e));var vt=ee("visit",Date.now());te("visit",Date.now());function bt(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var fe=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var Vt=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function ge(e){Y.set(e),je.set(e.theme),e.settings?.theme_mode&&O.set(e.settings.theme_mode),xe()}async function Ee(e,t){e==="theme_mode"&&(O.set(t),xe()),ge(await Je(e,t))}function yt(){let e=b(O),t=X(),n=b(Y),[s,i]=y(null);C(()=>{document.title="Settings \xB7 Beamtime"},[]);let r=(o,p)=>{i(null),Ee(o,p).catch(d=>i(d.message))},l=n?.settings??{};return a`<div class="page settings">
    <header class="header"><h1 class="title" tabindex="-1">Settings</h1></header>
    <p class="muted small">Changes are written to <code>${l.file??"beamtime.yaml"}</code>, the project's settings.</p>
    ${s?a`<${H} kind="error">${s}<//>`:null}
    <h2>Appearance</h2>
    <div class="settings-rows">
      <span class="field-label">Mode</span>
      <div class="segmented" role="radiogroup" aria-label="Theme mode">
        ${Vt.map(([o,p,d])=>a`<button type="button" role="radio" aria-checked=${e===o} onClick=${()=>r("theme_mode",o)}>
          <${m} name=${p} size=${15} />${d}</button>`)}
      </div>
      <span class="field-label">Theme</span>
      <select value=${l.theme} onChange=${o=>r("theme",o.target.value)}>
        ${(n?.themes??[]).map(o=>a`<option value=${o}>${o}</option>`)}
      </select>
    </div>
    <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files go in <code>themes/</code> next to beamtime.yaml.</p>
    ${(n?.theme?.problems??[]).map(o=>a`<${H} kind="warning">${o}<//>`)}
    <h2>Figures</h2>
    <div class="settings-rows">
      <span class="field-label">Style sheets</span>
      ${(n?.figure_styles??[]).length?a`<${Qe} options=${n.figure_styles} value=${l.figure_style??[]} label="Style sheets"
            placeholder="Add a style" onChange=${o=>r("figure_style",o)} />`:a`<span class="muted small"><code>${JSON.stringify(l.figure_style??[])}</code>; choosing others needs the figures
            extra: <code>uv add matplotlib scienceplots</code></span>`}
    </div>
    <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(l.figure_style??[])})</code>, in this order
      (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>.</p>
    <h2>Keyboard</h2>
    <table class="kv">${fe.map(([o,p])=>a`<tr><td><kbd>${o}</kbd></td><td>${p}</td></tr>`)}</table>
    <h2>About</h2>
    <table class="kv">
      <tr><td class="muted">version</td><td>${n?.version}</td></tr>
      <tr><td class="muted">root</td><td><code>${n?.root}</code></td></tr>
      <tr><td class="muted">log dir</td><td><code>${n?.logdir}</code></td></tr>
    </table>
  </div>`}var wt={system:"light",light:"dark",dark:"system"},Gt={system:"monitor",light:"sun",dark:"moon"};function kt(){let e=b(Y),t=b(O),n=b(M);return a`<header class="topbar">
    <${U} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>M.set(!n)} />
    <a class="project" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search" onClick=${()=>I.set("")} aria-label="Search (⌘K)">
      <${m} name="search" size=${15} /><span class="search-label">Search groups, runs, commands</span><kbd>⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${qt} />
      <${U} icon=${Gt[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${wt[t]})`}
        onClick=${()=>{Ee("theme_mode",wt[t])}} />
      <a class="icon-button" href=${dt(L.value.page==="group"?L.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${m} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${m} name="settings" size=${16} /></a>
    </div>
  </header>`}function qt(){let t=(h(j()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?a`${[{name:"local",state:"connected"},...t].map(n=>a`<a class=${`source ${n.state}`}
      href=${$(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${m} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:a`<span class="source" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${m} name="server" size=${15} /> local</span>`}function Wt(e){let[t,n]=y(Date.now());return C(()=>{let s=setInterval(()=>n(Date.now()),e);return()=>clearInterval(s)},[e]),t}function Xt(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function xt(){let e=b(_e),t=b(N),n=b(He),s=b(L),i=Wt(5e3),r=h(ot()).data,l=E(h($e()).data),o=b(Y),p=r?.daemon,d=r?.runs?.running??0,u=l.filter(x=>x["run.status"]==="failed"&&Xt(x["run.ended_at"])>vt).length,g=r?.meta?.freshness,[f,D,v]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&p?["",`live \xB7 updated ${_(new Date(n).toISOString(),i)}`,`beamtime serve, pid ${p.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return a`<footer class="statusbar">
    <span class="status-item" data-tip=${v}><span class=${`live-dot ${f}`}></span>${D}</span>
    ${d?a`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>I.set("running")}>
          <${m} name="circle-dot" size=${14} class="tone-running" />${d} running</button>`:null}
    ${u?a`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>I.set("failed")}>
          <${m} name="circle-x" size=${14} />${u} failed since your last visit</button>`:null}
    ${g?.behind?a`<span class="status-item warn-text" data-tip=${g.text}><${m} name="hourglass" size=${14} />${g.behind} runs behind</span>`:null}
    ${g?.damaged?.length?a`<span class="status-item warn-text" data-tip=${g.damaged.join(`
`)}><${m} name="triangle-alert" size=${14} />${g.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${s.page==="group"&&s.run?a`<span class="status-item"><${m} name="activity" size=${14} />1 run selected</span>`:null}
    <${U} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>N.set(!t)} />
    ${o?.outdated?a`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item subtle">${o?.version?`beamtime ${o.version}`:""}</span>
  </footer>`}function St(e){let t=()=>S($(e.path),{replace:!0});return a`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head">
      <span class="status-item"><${m} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${U} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?a`<${Yt} id=${e.run} scope=${e.path} />`:a`<${Jt} path=${e.path} />`}
  </aside>`}function Yt({id:e,scope:t}){let n=h(me(e,t)).data,s=h(st(e,t)).data,i=h(he(t)).data,r=X(),l=Q(()=>pe(E(i).map(d=>d["run.id"]),r).get(e),[i,r,e]);if(!n)return a`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let o=n.run,p=Object.entries(n.metrics??{});return a`<div class="drawer-body">
    <h3><span class="run-dot" style=${`background:${l??"var(--bt-subtle)"}`}></span>
      <a href=${se(e)}>${o.name}</a></h3>
    <p class="facts small">
      <${w} spec=${k("run",o.status)} word />
      <span class="fact"><b>${ce(o.steps)}</b> steps</span>
      <span class="fact"><b>${de(o.duration_s)}</b></span>
      <span class="fact" data-tip=${o.created_at}>${_(o.created_at)}</span>
    </p>
    ${o.error?a`<pre class="log bad-text">${o.error}</pre>`:null}
    <h4>Config</h4>
    <table class="kv">${Object.entries(n.config??{}).map(([d,u])=>a`<tr><td>${d}</td><td class="num">${P(u)}</td></tr>`)}</table>
    ${p.length?a`<h4>Metrics</h4>
          <table class="kv">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${p.map(([d,u])=>a`<tr><td>${d}</td><td class="num"><b>${P(u.last)}</b></td>
              <td class="num">${P(u.min)}</td><td class="num">${P(u.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?a`<h4>Cited by</h4>${n.cited_by.map(d=>a`<p class="small"><${w} spec=${k("note",d.type)} /> ${d.description}</p>`)}`:null}
    <h4>Events</h4>
    ${(n.events??[]).slice(-8).map(d=>a`<div class="event"><span class="muted num">${d.t?.slice(5,16).replace("T"," ")}</span>
        <${m} name=${Te(d.type)} size=${14} /><span>${d.description}</span></div>`)}
    <h4>Output</h4>
    <pre class="log">${(s?.lines??[]).join(`
`)}</pre>
  </div>`}function Jt({path:e}){let t=h(at(e)).data,n=h(rt(e)).data;return a`<div class="drawer-body">
    <h4 style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?a`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(s=>!String(s.state??"").startsWith("superseded")).map(s=>a`<${mt} key=${s.id} note=${s} />`)}</div>
    <h4>Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(s=>a`<div class="event"><span class="muted num">${s.t?.slice(5,16).replace("T"," ")}</span>
        <${m} name=${s.kind==="note"?"file-text":Te(s.type)} size=${14} />
        <span>${s.run?a`<a href=${se(s.run)}>${s.run.slice(-8)}</a> `:null}${s.description??s.type}</span></div>`)}
  </div>`}var Ce=["failed","killed","lost"];function Le(e){let t=le(e.path),n=t==="."?e.path:e.path.slice(t.length+1),s=R(e.path)?[]:n.split("/"),i=s.length&&ke(s[s.length-1])?s[s.length-1]:null,r=s.slice(0,-1),l=o=>[...t==="."?[]:[t],...r.slice(0,o+1)].join("/");return a`<header class="header">
    <nav class="crumbs" aria-label="Breadcrumb">
      ${s.length?a`<a href=${$(t)}>${t==="."?"local":t}</a>`:null}
      ${r.map((o,p)=>a`<span class="sep">/</span><a href=${$(l(p))}>${o}</a>`)}
    </nav>
    ${i?a`<${Zt} id=${i} scope=${e.path} />`:a`<${Qt} path=${e.path} />`}
    ${e.finding?a`<p class="finding">${e.finding}</p>`:null}
  </header>`}function Qt({path:e}){let t=E(h(et(e)).data)[0]??null,n=h(t?.proposal?tt(e):null).data,s=h(t?.proposal?nt(e):null).data,i=s?.proposal?.rationale,r=s?.versions?.find(u=>u.version===s.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,l=e==="."?"local":e.split("/").pop();if(!t)return a`<h1 class="title" tabindex="-1">${l}</h1><div class="skeleton late" style="block-size: 52px"></div>`;let[o,p]=pt(n?.progress?.text??t.progress),d=Ce.reduce((u,g)=>u+(t[g]??0),0);return a`
    <h1 class="title" tabindex="-1">${l} <${w} spec=${k("research",t.status)} word /></h1>
    ${t.proposal?a`<div class="statement">
          <${Se} value=${t.proposal} label="the proposal's statement" locked=${s?r:"Loading the proposal\u2026"}
            render=${u=>a`<span data-tip=${r?void 0:i}>${u}</span>`}
            onSave=${u=>Ge(e,u)} />
        </div>`:null}
    ${t.proposal?a`<div class="preds">
          ${(n?.predictions??[]).map(u=>a`<span class="pred" key=${u.name} data-tip=${ut(u)}>
              <${w} spec=${k("result",u.result)} /><b>${u.name}</b></span>`)}
          ${n?.provisional?a`<span class="tag tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
          ${o?a`<span class="pred"><${Fe} fraction=${n?.progress?.fraction??null} label=${p??o} />
                <span data-tip=${p}>${o}</span></span>`:null}
          ${t.verdict?a`<span class="pred"><${w} spec=${k("verdict",t.verdict)} word /></span>`:null}
        </div>`:null}
    <div class="facts">
      <span class="fact"><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?a`<span class="fact"><${w} spec=${k("run","running")} /><b>${t.running}</b> running</span>`:null}
      ${t.finished?a`<span class="fact"><${w} spec=${k("run","finished")} /><b>${t.finished}</b> finished</span>`:null}
      ${d?a`<span class="fact tone-bad" data-tip=${Ce.filter(u=>t[u]).map(u=>`${t[u]} ${u}`).join(", ")}>
            <${m} name="circle-x" size=${15} /><b class="tone-bad">${d}</b> ${d===1?Ce.find(u=>t[u]):"ended early"}</span>`:null}
      ${t.notes?a`<span class="fact"><${m} name="file-text" size=${15} /><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${Tt} path=${e} />
    </div>`}function Zt({id:e,scope:t}){let n=h(me(e,t)).data;if(!n)return a`<h1 class="title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 52px"></div>`;let s=n.run,i=()=>{navigator.clipboard?.writeText(s.id)};return a`
    <h1 class="title" tabindex="-1"><${Se} value=${s.name??s.id} label="the run's name" class="title-edit"
        onSave=${r=>qe(s.id,t,r.trim())} />
      <${w} spec=${k("run",s.status)} word /></h1>
    ${s.error?a`<p class="statement bad-text" data-tip=${s.error}>${s.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span class="fact"><b>${ce(s.steps)}</b> steps</span>
      <span class="fact"><b>${de(s.duration_s)}</b></span>
      <span class="fact" data-tip=${s.created_at}>${_(s.created_at)}</span>
      <${Tt} path=${t} />
      <span class="fact">
        <${U} icon="copy" label=${`Copy the run id ${s.id}`} onClick=${i} />
        <${Ve} icon="ellipsis" label="Details" title="Run details" class="run-details">
          <table class="kv">${en(s).map(([r,l])=>a`<tr><td class="muted">${r}</td><td>${l}</td></tr>`)}</table>
          <div class="menu-list">
            <button type="button" onClick=${()=>S($(t,{run:s.id}),{replace:!0})}>
              <${m} name="panel-right" size=${15} /> Open in the side panel</button>
            <button type="button" onClick=${i}><${m} name="copy" size=${15} /> Copy the run id</button>
            ${s.git?.commit?a`<button type="button" onClick=${()=>navigator.clipboard?.writeText(s.git.commit)}>
              <${m} name="git-commit" size=${15} /> Copy the commit</button>`:null}
          </div>
        <//>
      </span>
    </div>
    ${(n.proposals??[]).length?a`<div class="preds" style="margin-block-start: 10px">
          ${n.proposals.map(r=>a`<a class="pred" href=${$(r.group)} data-tip=${r.statement}>
              <${w} spec=${k("result",r.check)} /><b>${r.group==="."?"own proposal":r.group}</b>
              ${r.verdict?a`<${w} spec=${k("verdict",r.verdict)} />`:null}</a>`)}
        </div>`:null}`}function Tt({path:e}){let t=h(Ze(e)).data?.summary;if(!t)return null;let n=Object.entries(t.config??{}).map(([i,r])=>`${i} ${P(r)}`).join(", "),s=ke(e.split("/").pop()??"");return a`<span class="fact" data-tip=${`${t.stat} of ${t.metric} over ${s?"the run":"all runs"}`}>
    best <b>${t.metric} ${P(t.value)}</b>
    ${s?null:a`<span>· <a href=${se(t.run)}>${t.name}</a>${n?a` <em>(${n})</em>`:null}</span>`}
  </span>`}function en(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,s])=>[n,String(s)])}function Et(e,t){let n=e.split(`
`),s=t.split(`
`),i=n.length,r=s.length,l=Array.from({length:i+1},()=>new Uint32Array(r+1));for(let u=i-1;u>=0;u--)for(let g=r-1;g>=0;g--)l[u][g]=n[u]===s[g]?l[u+1][g+1]+1:Math.max(l[u+1][g],l[u][g+1]);let o=[],p=0,d=0;for(;p<i&&d<r;)n[p]===s[d]?(o.push({kind:"same",text:n[p]}),p++,d++):l[p+1][d]>=l[p][d+1]?o.push({kind:"removed",text:n[p++]}):o.push({kind:"added",text:s[d++]});for(;p<i;)o.push({kind:"removed",text:n[p++]});for(;d<r;)o.push({kind:"added",text:s[d++]});return o}function Ct(e,t=3){let n=[],s=0;for(;s<e.length;){if(e[s].kind!=="same"){n.push(e[s++]);continue}let i=s;for(;i<e.length&&e[i].kind==="same";)i++;let r=s===0?0:t,l=i===e.length?0:t;i-s>r+l+1?n.push(...e.slice(s,s+r),{kind:"skip",count:i-s-r-l},...e.slice(i-l,i)):n.push(...e.slice(s,i)),s=i}return n}function ve(e){let t=h(he(e.path)),n=X(),s=E(t.data),i=Q(()=>pe(s.map(o=>o["run.id"]),n),[t.data,n]),r=Q(()=>new Map(s.map(o=>[o["run.id"],o["run.name"]??o["run.id"]])),[t.data]);if(!e.view)return a`<div class="view"><div class="skeleton late" style="block-size: 320px"></div></div>`;let l={path:e.path,colors:i,names:r,metrics:e.view.metrics??{}};return a`<div class="view"><${Ke.Provider} value=${l}><${gt} node=${e.view.view} /><//></div>`}function Lt(e){let t=e.view,n=b(L),s=n.page==="group"&&n.version,i=t.versions?a`<a href=${$(e.path,{history:!0})}><${m} name="history" size=${14} /> history (${t.versions})</a>`:null,r;switch(t.source){case"draft":r=a`draft <b>${t.draft}</b>`;break;case"view":r=a`${t.title?a`<em>${t.title}</em> · `:null}saved ${_(Me(t.version))} by ${t.author??"unknown"}`;break;default:r=a`the built-in view`}return a`<div class="view-source">
    <${m} name="layout" size=${14} /><span>${r}</span>
    ${s?a`<a href=${$(e.path)}>an older version · show the current one</a>`:null}
    ${i}
    ${t.outdated?.length&&!s?a`<${tn} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||s?null:a`<${nn} path=${e.path} />
        <${sn} path=${e.path} view=${t} />`}
  </div>`}function tn(e){let[t,n]=y(null),s=e.outdated.map(r=>r.name).join(", ");return a`<button type="button" class="link small" onClick=${async()=>{n(null);try{await Xe(e.path)}catch(r){n(r.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${s} exists; update re-pins this view to it (a new version)`}>
      <${m} name="update" size=${14} /> update ${s}</button>
    ${t?a`<span class="bad-text small">${t}</span>`:null}`}function nn(e){let[t,n]=y(null);return a`<button type="button" class="link small" onClick=${async()=>{n(null);try{Ye.set(await We(e.path,null,""))}catch(i){n(i.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${m} name="file-text" size=${14} /> add text</button>
    ${t?a`<span class="bad-text small">${t}</span>`:null}`}function sn(e){let t=ht(e.path),n=ft(t),[s,i]=y(!1),[r,l]=y(e.view.title??""),[o,p]=y(e.view.finding??""),[d,u]=y(null),[g,f]=y(!1);if(!n&&!s)return null;let D=async v=>{v.preventDefault(),f(!0),u(null);try{let x={charts:t.charts,added:t.added,order:t.order,spans:t.spans};await ne("save_view",{path:e.path,prefs:x,title:r,finding:o}),$t(e.path,()=>({view:{},charts:{},added:[],order:{},spans:{}})),Ae(q=>["view","view_history","summary"].includes(q.method)&&q.scope===e.path),i(!1)}catch(x){u(x.message)}finally{f(!1)}};return s?a`<form class="save-form" onSubmit=${D}>
    <label class="field"><span class="field-label">Title</span>
      <input value=${r} onInput=${v=>l(v.target.value)} /></label>
    <label class="field"><span class="field-label">Finding</span>
      <input value=${o} placeholder="the key result in one sentence"
        onInput=${v=>p(v.target.value)} /></label>
    <div class="save-actions">
      <button type="submit" class="button primary" disabled=${g}>${g?"Saving\u2026":"Save as view"}</button>
      <button type="button" class="link small" onClick=${()=>i(!1)}>cancel</button>
      ${d?a`<span class="bad-text small">${d}</span>`:null}
    </div>
  </form>`:a`<button type="button" class="link small save-view" onClick=${()=>i(!0)}
        data-tip="Save your chart settings and added charts as this page's view, for everyone">
      <${m} name="save" size=${14} /> Save as view</button>`}function Mt(e){let t=h(lt(e.path)),n=t.data?.entries??[],[s,i]=y(null),r=s??n.slice(0,2).map(o=>o.version).reverse(),l=o=>{let p=r.includes(o)?r.filter(d=>d!==o):[...r,o].slice(-2);i(p.sort())};return t.status==="error"?a`<${H} kind="error">${t.error}<//>`:a`<section class="history">
    <h2 class="history-title"><${m} name="history" size=${18} /> View history</h2>
    ${t.data&&!n.length?a`<${H}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((o,p)=>a`<li key=${o.version} class=${r.includes(o.version)?"picked":""}>
          <label><input type="checkbox" checked=${r.includes(o.version)} onChange=${()=>l(o.version)} />
            <span class="num muted" data-tip=${o.version}>${_(o.time)}</span>
            <b>${o.title??"untitled"}</b><span class="muted">${o.author??""}</span>
            ${o.message?a`<span>${o.message}</span>`:null}</label>
          <a href=${p===0?$(e.path):$(e.path,{version:o.version})}
            onClick=${d=>{d.preventDefault(),S(p===0?$(e.path):$(e.path,{version:o.version}))}}>${p===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${r.length===2?a`<${an} path=${e.path} a=${r[0]} b=${r[1]} />`:null}
  </section>`}function an(e){let t=o=>({method:"view_show",params:{group:e.path,version:o},scope:e.path}),n=h(t(e.a)).data,s=h(t(e.b)).data,i=h(V(e.path,e.a)).data,r=h(V(e.path,e.b)).data,l=n&&s?Ct(Et(n.yaml,s.yaml)):[];return a`<div class="compare">
    <h3 class="block-title">Changes from ${_(Me(e.a))} to ${_(Me(e.b))}</h3>
    <pre class="diff">${l.map(o=>o.kind==="skip"?a`<div class="diff-skip">⋯ ${o.count} unchanged lines</div>`:a`<div class=${`diff-${o.kind}`}>${o.kind==="added"?"+ ":o.kind==="removed"?"\u2212 ":"  "}${o.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title">${i?.title??e.a}</h3><${ve} path=${e.path} view=${i} /></div>
      <div><h3 class="block-title">${r?.title??e.b}</h3><${ve} path=${e.path} view=${r} /></div>
    </div>
  </div>`}function Me(e){return e?`${e.slice(0,4)}-${e.slice(4,6)}-${e.slice(6,8)}T${e.slice(9,11)}:${e.slice(11,13)}:${e.slice(13,15)}Z`:null}function It(e){return C(()=>{document.title=`${e.path==="."?"local":e.path} \xB7 Beamtime`},[e.path]),e.history?a`<div class="page"><${Le} path=${e.path} /><${Mt} path=${e.path} /></div>`:a`<div class="page">
    <${rn} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function rn(e){let t=h(V(e.path,e.version,e.draft));return C(()=>{t.status==="ready"&&requestAnimationFrame(Pe)},[t.status==="ready"]),a`
    <${Le} path=${e.path} finding=${t.data?.finding} />
    ${t.data?a`<${Lt} path=${e.path} view=${t.data} />`:null}
    ${t.status==="error"?on(e.path,t.error)?a`<${H} kind="warning">${t.error} The page fills in once the remote answers again.<//>`:a`<${H} kind="error">${t.error}<//>`:a`<${ve} path=${e.path} view=${t.data} />`}`}function on(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function Dt(e){C(()=>{ie(V(e.id)).then(n=>S($(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=h(V(e.id));return t.status==="error"?a`<div class="page"><${H} kind="error">${t.error}<//></div>`:a`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}function Rt(e,t){let n=e.toLowerCase(),s=t.toLowerCase();if(!n)return 1;let i=s.indexOf(n);if(i>=0)return 100-Math.min(i,50)-s.length/100;let r=0,l=0;for(let o of s)if(o===n[r]?r++:r>0&&l++,r===n.length)return 40-Math.min(l,39);return 0}function Nt(e){let[t,n]=y(e.query),[s,i]=y(0),r=F(null),l=E(h(j()).data),o=E(h($e()).data);C(()=>{let c=r.current;c.showModal();let z=()=>I.set(null);c.addEventListener("close",z);let K=!1,re=B=>{let oe=c.getBoundingClientRect();return B.clientX<oe.left||B.clientX>oe.right||B.clientY<oe.top||B.clientY>oe.bottom},De=B=>K=re(B),Re=B=>K&&re(B)&&c.close();return"closedBy"in HTMLDialogElement.prototype||(c.addEventListener("pointerdown",De),c.addEventListener("pointerup",Re)),()=>{c.removeEventListener("close",z),c.removeEventListener("pointerdown",De),c.removeEventListener("pointerup",Re)}},[]);let p=()=>r.current?.close(),d=c=>()=>S(c),u=L.value,g=u.page==="group"?u.path:".",f=(c,z,K,re)=>({section:"Commands",label:c,detail:z,sym:{icon:K,tone:"muted",label:c},run:re}),v=[...l.map(c=>({section:"Groups",label:c.path==="."?"local":c.path,detail:`${c.runs} runs${c.proposal?` \xB7 ${c.proposal}`:""}`,sym:k("research",c.status),run:d($(c.path))})),...o.map(c=>({section:"Runs",label:c["run.name"]??c["run.id"],detail:`${c["run.status"]} \xB7 ${c["run.path"]}`,sym:k("run",c["run.status"]),run:d($(c["run.path"]))})),f("Theme: light","","sun",()=>ue("light")),f("Theme: dark","","moon",()=>ue("dark")),f("Theme: follow the system","","monitor",()=>ue("system")),f("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),f("Show notes and timeline","i","file-text",d($(g,{drawer:!0}))),f("Show or hide the sidebar","\u2318B","panel-left",()=>M.set(!M.value)),f(N.value?"Resume live updates":"Pause live updates","p",N.value?"play":"pause",()=>N.set(!N.value)),f("Keyboard shortcuts","?","keyboard",()=>A.set(!0)),f("Settings","","settings",d("/settings/appearance"))].map(c=>({it:c,s:Math.max(Rt(t,c.label),Rt(t,c.detail)*.5)})).filter(c=>c.s>0).sort((c,z)=>z.s-c.s||zt(c.it.section)-zt(z.it.section)).slice(0,60).map(c=>c.it),x=c=>{c&&(p(),c.run())},q=c=>{if(c.key==="ArrowDown")i(Math.min(v.length-1,s+1));else if(c.key==="ArrowUp")i(Math.max(0,s-1));else if(c.key==="Enter")x(v[s]);else return;c.preventDefault()},Ie="";return a`<dialog class="sheet" ref=${r} aria-label="Search" closedby="any">
    <div class="palette-input"><${m} name="search" size=${18} />
      <input autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${v[s]?`pal-${s}`:void 0}
        onInput=${c=>{n(c.target.value),i(0)}} onKeyDown=${q} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${v.map((c,z)=>{let K=c.section!==Ie&&!t?Ie=c.section:null;return a`${K?a`<li class="section" role="presentation">${K}</li>`:null}
          <li id=${`pal-${z}`} class="item" role="option" aria-selected=${z===s}
              onMouseMove=${()=>i(z)} onClick=${()=>x(c)}>
            <${w} spec=${c.sym} /><span class="label">${c.label}</span><span class="detail">${c.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function zt(e){return["Groups","Runs","Commands"].indexOf(e)}function be(e,t=[]){let n=new Map,s=(r,l={})=>({path:r,name:r==="."?"local":r.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let r of e)n.set(r.path,s(r.path,r));n.has(".")||n.set(".",s("."));for(let r of t)r.name!=="local"&&(n.has(r.name)||n.set(r.name,s(r.name)),Object.assign(n.get(r.name),{state:r.state,error:r.error}));for(let r of n.values()){if(R(r.path))continue;let l=r.path.lastIndexOf("/"),o=l<0?".":r.path.slice(0,l);(n.get(o)??n.get(le(r.path))??n.get(".")).children.push(r)}for(let r of n.values())r.children.sort((l,o)=>l.name.localeCompare(o.name));let i=[...n.values()].filter(r=>r.path!=="."&&R(r.path)).sort((r,l)=>r.name.localeCompare(l.name));return[n.get("."),...i]}function _t(e,t,n){let s=[],i=n.toLowerCase(),r=l=>{(!i||l.path.toLowerCase().includes(i)||Ht(l,i))&&(s.push(l),(i||t.has(l.path)||R(l.path))&&l.children.forEach(r))};return e.forEach(r),s}function Ht(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||Ht(n,t))}function Ot(e,t){if(R(t))return e;let n=t.lastIndexOf("/"),s=n<0?".":t.slice(0,n),i=r=>r.path===s?r:r.children.map(i).find(l=>l)??null;return e.map(i).find(r=>r)?.children??[]}function At(e){return R(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function Bt(){let e=b(L),t=h(j()),[n,s]=y(()=>new Set(ee("open",[]))),[i,r]=y(""),l=F(null),o=e.page==="group"?e.path:null,p=be(E(t.data),t.data?.meta?.sources??[]),d=_t(p,dn(n,o),i),u=(f,D)=>{let v=new Set(n);D??!v.has(f)?v.add(f):v.delete(f),te("open",[...v]),s(v)};return a`<nav class="sidebar" aria-label="Groups">
    <label class="filter"><${m} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${i} aria-label="Filter groups"
        onInput=${f=>r(f.target.value)} />
    </label>
    <div class="tree" ref=${l} onKeyDown=${f=>{let D=[...l.current?.querySelectorAll("a.tree-item")??[]],v=D.indexOf(document.activeElement),x=d[v];switch(f.key){case"ArrowDown":D[Math.min(D.length-1,v+1)]?.focus();break;case"ArrowUp":D[Math.max(0,v-1)]?.focus();break;case"ArrowRight":x?.children.length&&u(x.path,!0);break;case"ArrowLeft":x&&n.has(x.path)?u(x.path,!1):x&&D[d.findIndex(q=>q.path===cn(x.path))]?.focus();break;default:return}f.preventDefault()}} role="tree">
      ${d.map(f=>a`<${ln} key=${f.path} node=${f} current=${f.path===o}
        open=${n.has(f.path)||!!i} onToggle=${()=>u(f.path)} />`)}
    </div>
  </nav>`}function ln(e){let t=e.node,n=()=>it(t.path),s=t.children.length>0&&!R(t.path);return a`<a class=${`tree-item${e.current?" current":""}${t.path.startsWith("@")&&R(t.path)?" source-root":""}`} href=${$(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${s?e.open:void 0}
      style=${`padding-inline-start:${6+At(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${i=>{i.metaKey||i.ctrlKey||(i.preventDefault(),S($(t.path)))}}>
    <span class="twisty" onClick=${i=>{i.preventDefault(),i.stopPropagation(),e.onToggle()}}>
      ${s?a`<${m} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    <span class="tree-name">${t.name}</span>
    ${t.state==="unreachable"?a`<${w} spec=${{icon:"cloud-off",tone:"muted",label:`Unreachable: ${t.error??"no answer"}`}} size=${13} />`:null}
    <span class="tree-marks">
      ${t.running?a`<${w} spec=${k("run","running")} size=${13} />`:null}
      ${t.failed?a`<${w} spec=${{...k("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${13} />`:null}
    </span>
    <span class="count">${t.runs||""}</span>
  </a>`}function cn(e){if(R(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function dn(e,t){if(!t||t===".")return e;let n=new Set(e),s=t.split("/");for(let i=1;i<s.length;i++)n.add(s.slice(0,i).join("/"));return n}function Ut(){let e=b(L),t=b(M),n=b(I),s=b(A),i=F(null);C(()=>Be(()=>i.current),[]),C(()=>(addEventListener("keydown",Pt),()=>removeEventListener("keydown",Pt)),[]);let r=e.page==="group"&&e.drawer,l;switch(e.page){case"group":l=a`<${It} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":l=a`<${Dt} id=${e.id} />`;break;case"settings":l=a`<${yt} />`;break;case"timeline":l=a`<${ct} key=${e.from} from=${e.from} />`;break;default:l=a`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return W?a`<main class="main render-main" ref=${i}>${l}</main>`:a`<div class=${`shell${t?"":" no-sidebar"}${r?" with-drawer":""}`}>
    <${kt} />
    ${t?a`<${Bt} />`:null}
    <main class="main" ref=${i}>${l}</main>
    ${r?a`<${St} path=${e.path} run=${e.run} />`:null}
    <${xt} />
    ${n!==null?a`<${Nt} query=${n} />`:null}
    ${s?a`<${pn} />`:null}
  </div>`}function Pt(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),I.set(I.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),M.set(!M.value);return}if(e.key==="Escape"){if(I.value!==null||A.value)return;let s=L.value;return s.page==="group"&&s.run?S($(s.path,{drawer:!0}),{replace:!0}):s.page==="group"&&s.drawer?S($(s.path),{replace:!0}):void 0}if(t||e.altKey||bt(e)||I.value!==null||A.value)return;let n=L.value;switch(e.key){case"/":e.preventDefault(),I.set("");break;case"?":A.set(!A.value);break;case"p":N.set(!N.value);break;case"i":n.page==="group"&&S($(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":M.set(!M.value);break;case"[":case"]":n.page==="group"&&un(n.path,e.key==="]"?1:-1);break}}async function un(e,t){let n=await ie(j()),s=Ot(be(E(n),n?.meta?.sources??[]),e),i=s.findIndex(l=>l.path===e),r=s[i+t];r&&S($(r.path))}function pn(){let e=F(null);return C(()=>{let t=e.current;t.showModal();let n=()=>A.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),a`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${fe.map(([t,n])=>a`<tr><td><kbd>${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 14px"><button class="link" autofocus>Close</button></form>
    </div>
  </dialog>`}var T=null,J=null,ye,ae;function Ft(){T=document.createElement("div"),T.className="bt-hint",T.setAttribute("popover","manual"),T.id="bt-hint",document.body.append(T),T.addEventListener("pointerenter",()=>clearTimeout(ae)),T.addEventListener("pointerleave",()=>Kt()),document.addEventListener("pointerover",e=>{let t=e.target.closest?.("[data-tip]");t&&t!==J&&(clearTimeout(ye),ye=setTimeout(()=>jt(t),J?0:350))}),document.addEventListener("pointerout",e=>{let t=e.target.closest?.("[data-tip]");t&&(clearTimeout(ye),t===J&&Kt())}),document.addEventListener("focusin",e=>{let t=e.target.closest?.("[data-tip]");t&&e.target.matches(":focus-visible")&&jt(t)}),document.addEventListener("focusout",()=>we()),document.addEventListener("keydown",e=>{e.key==="Escape"&&J&&we()}),document.addEventListener("pointerdown",()=>we(),!0)}function jt(e){let t=e.getAttribute("data-tip");if(!T||!t||!e.isConnected)return;clearTimeout(ae),J=e,T.textContent=t,T.matches(":popover-open")||T.showPopover();let n=e.getBoundingClientRect(),s=T.getBoundingClientRect(),i=6,r=n.top-s.height-i,l=r>=4?r:n.bottom+i,o=Math.min(Math.max(4,n.left+n.width/2-s.width/2),innerWidth-s.width-4);T.style.top=`${l}px`,T.style.left=`${o}px`}function Kt(){clearTimeout(ae),ae=setTimeout(we,120)}function we(){clearTimeout(ye),clearTimeout(ae),J=null,T?.matches(":popover-open")&&T.hidePopover()}Ue();if(W){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(O.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Ne.n}Ft();var mn=ne("meta").then(e=>(W&&(e={...e,settings:{...e.settings,theme_mode:O.value}}),ge(e),e));W||Oe(async()=>{let[e,t]=await Promise.all([mn,ne("meta")]);e.bundle!==t.bundle?location.reload():ge(t)});ze(a`<${Ut} />`,document.getElementById("app"));
