import{$ as ue,A as Ue,Aa as ot,B as Se,Ba as it,C as $,Ca as lt,D as se,Da as fe,E as le,Ea as ct,F as R,Fa as dt,G as L,Ga as ut,H as je,Ha as pt,Ia as Te,J as S,Ja as k,K as Ke,Ka as Ce,L as Fe,La as mt,M as W,Ma as ht,N as U,Na as $t,O as ce,P as de,Q as _,Qa as ft,Ra as gt,Sa as vt,Ta as Le,Ua as ge,X as Ve,Y as B,_ as Ee,aa as pe,ba as X,c as He,ca as me,d as a,da as m,e as y,ea as w,f as E,fa as H,g as O,ga as C,h as Q,ha as j,ia as Ge,ja as qe,ka as We,l as Z,la as Xe,m as g,ma as Ye,n as ee,na as Je,o as te,oa as Qe,pa as Ze,qa as et,r as ne,ra as K,s as Oe,sa as V,t as ie,ta as tt,u as h,ua as nt,va as st,w as z,wa as at,x as Be,xa as he,y as Pe,ya as rt,z as Ae,za as $e}from"./chunks/chunk-KVFUMXKO.js";import"./chunks/chunk-EBVYA7LM.js";import"./chunks/chunk-VC46IEJQ.js";var M=new Z(ee("sidebar",!0)),I=new Z(null),P=new Z(!1),Y=new Z(null);M.subscribe(e=>te("sidebar",e));var bt=ee("visit",Date.now());te("visit",Date.now());function yt(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var ve=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var qt=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function be(e){Y.set(e),Ve.set(e.theme),e.settings?.theme_mode&&B.set(e.settings.theme_mode),Ee()}async function Me(e,t){e==="theme_mode"&&(B.set(t),Ee()),be(await Ze(e,t))}function wt(){let e=g(B),t=X(),n=g(Y),[s,o]=y(null);E(()=>{document.title="Settings \xB7 Beamtime"},[]);let r=(i,p)=>{o(null),Me(i,p).catch(d=>o(d.message))},l=n?.settings??{};return a`<div class="page settings">
    <header class="header"><h1 class="title" tabindex="-1">Settings</h1></header>
    <p class="muted small">Changes are written to <code>${l.file??"beamtime.yaml"}</code>, the project's settings.</p>
    ${s?a`<${H} kind="error">${s}<//>`:null}
    <h2>Appearance</h2>
    <div class="settings-rows">
      <span class="field-label">Mode</span>
      <div class="segmented" role="radiogroup" aria-label="Theme mode">
        ${qt.map(([i,p,d])=>a`<button type="button" role="radio" aria-checked=${e===i} onClick=${()=>r("theme_mode",i)}>
          <${m} name=${p} size=${15} />${d}</button>`)}
      </div>
      <span class="field-label">Theme</span>
      <select value=${l.theme} onChange=${i=>r("theme",i.target.value)}>
        ${(n?.themes??[]).map(i=>a`<option value=${i}>${i}</option>`)}
      </select>
    </div>
    <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files go in <code>themes/</code> next to beamtime.yaml.</p>
    ${(n?.theme?.problems??[]).map(i=>a`<${H} kind="warning">${i}<//>`)}
    <h2>Figures</h2>
    <div class="settings-rows">
      <span class="field-label">Style sheets</span>
      ${(n?.figure_styles??[]).length?a`<${et} options=${n.figure_styles} value=${l.figure_style??[]} label="Style sheets"
            placeholder="Add a style" onChange=${i=>r("figure_style",i)} />`:a`<span class="muted small"><code>${JSON.stringify(l.figure_style??[])}</code>; choosing others needs the figures
            extra: <code>uv add matplotlib scienceplots</code></span>`}
    </div>
    <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(l.figure_style??[])})</code>, in this order
      (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
      <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <h2>Keyboard</h2>
    <table class="kv">${ve.map(([i,p])=>a`<tr><td><kbd>${i}</kbd></td><td>${p}</td></tr>`)}</table>
    <h2>About</h2>
    <table class="kv">
      <tr><td class="muted">version</td><td>${n?.version}</td></tr>
      <tr><td class="muted">root</td><td><code>${n?.root}</code></td></tr>
      <tr><td class="muted">log dir</td><td><code>${n?.logdir}</code></td></tr>
    </table>
  </div>`}var kt={system:"light",light:"dark",dark:"system"},Wt={system:"monitor",light:"sun",dark:"moon"};function xt(){let e=g(Y),t=g(B),n=g(M);return a`<header class="topbar">
    <${j} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>M.set(!n)} />
    <a class="project" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search" onClick=${()=>I.set("")} aria-label="Search (⌘K)">
      <${m} name="search" size=${15} /><span class="search-label">Search groups, runs, commands</span><kbd>⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${Xt} />
      <${j} icon=${Wt[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${kt[t]})`}
        onClick=${()=>{Me("theme_mode",kt[t])}} />
      <a class="icon-button" href=${pt(L.value.page==="group"?L.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${m} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${m} name="settings" size=${16} /></a>
    </div>
  </header>`}function Xt(){let t=(h(K()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?a`${[{name:"local",state:"connected"},...t].map(n=>a`<a class=${`source ${n.state}`}
      href=${$(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${m} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:a`<span class="source" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${m} name="server" size=${15} /> local</span>`}function Yt(e){let[t,n]=y(Date.now());return E(()=>{let s=setInterval(()=>n(Date.now()),e);return()=>clearInterval(s)},[e]),t}function Jt(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function St(){let e=g(Be),t=g(z),n=g(Pe),s=g(L),o=Yt(5e3),r=h(lt()).data,l=C(h(fe()).data),i=g(Y),p=r?.daemon,d=r?.runs?.running??0,u=l.filter(x=>x["run.status"]==="failed"&&Jt(x["run.ended_at"])>bt).length,v=r?.meta?.freshness,[f,D,b]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&p?["",`live \xB7 updated ${_(new Date(n).toISOString(),o)}`,`beamtime serve, pid ${p.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return a`<footer class="statusbar">
    <span class="status-item" data-tip=${b}><span class=${`live-dot ${f}`}></span>${D}</span>
    ${d?a`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>I.set("running")}>
          <${m} name="circle-dot" size=${14} class="tone-running" />${d} running</button>`:null}
    ${u?a`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>I.set("failed")}>
          <${m} name="circle-x" size=${14} />${u} failed since your last visit</button>`:null}
    ${v?.behind?a`<span class="status-item warn-text" data-tip=${v.text}><${m} name="hourglass" size=${14} />${v.behind} runs behind</span>`:null}
    ${v?.damaged?.length?a`<span class="status-item warn-text" data-tip=${v.damaged.join(`
`)}><${m} name="triangle-alert" size=${14} />${v.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${s.page==="group"&&s.run?a`<span class="status-item"><${m} name="activity" size=${14} />1 run selected</span>`:null}
    <${j} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>z.set(!t)} />
    ${i?.outdated?a`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item subtle">${i?.version?`beamtime ${i.version}`:""}</span>
  </footer>`}function Et(e){let t=()=>S($(e.path),{replace:!0});return a`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head">
      <span class="status-item"><${m} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${j} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?a`<${Qt} id=${e.run} scope=${e.path} />`:a`<${Zt} path=${e.path} />`}
  </aside>`}function Qt({id:e,scope:t}){let n=h(he(e,t)).data,s=h(rt(e,t)).data,o=h($e(t)).data,r=X(),l=Q(()=>me(C(o).map(d=>d["run.id"]),r).get(e),[o,r,e]);if(!n)return a`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let i=n.run,p=Object.entries(n.metrics??{});return a`<div class="drawer-body">
    <h3><span class="run-dot" style=${`background:${l??"var(--bt-subtle)"}`}></span>
      <a href=${se(e)}>${i.name}</a></h3>
    <p class="facts small">
      <${w} spec=${k("run",i.status)} word />
      <span class="fact"><b>${ce(i.steps)}</b> steps</span>
      <span class="fact"><b>${de(i.duration_s)}</b></span>
      <span class="fact" data-tip=${i.created_at}>${_(i.created_at)}</span>
    </p>
    ${i.error?a`<pre class="log bad-text">${i.error}</pre>`:null}
    <h4>Config</h4>
    <table class="kv">${Object.entries(n.config??{}).map(([d,u])=>a`<tr><td>${d}</td><td class="num">${U(u)}</td></tr>`)}</table>
    ${p.length?a`<h4>Metrics</h4>
          <table class="kv">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${p.map(([d,u])=>a`<tr><td>${d}</td><td class="num"><b>${U(u.last)}</b></td>
              <td class="num">${U(u.min)}</td><td class="num">${U(u.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?a`<h4>Cited by</h4>${n.cited_by.map(d=>a`<p class="small"><${w} spec=${k("note",d.type)} /> ${d.description}</p>`)}`:null}
    <h4>Events</h4>
    ${(n.events??[]).slice(-8).map(d=>a`<div class="event"><span class="muted num">${d.t?.slice(5,16).replace("T"," ")}</span>
        <${m} name=${Ce(d.type)} size=${14} /><span>${d.description}</span></div>`)}
    <h4>Output</h4>
    <pre class="log">${(s?.lines??[]).join(`
`)}</pre>
  </div>`}function Zt({path:e}){let t=h(ot(e)).data,n=h(it(e)).data;return a`<div class="drawer-body">
    <h4 style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?a`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(s=>!String(s.state??"").startsWith("superseded")).map(s=>a`<${$t} key=${s.id} note=${s} />`)}</div>
    <h4>Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(s=>a`<div class="event"><span class="muted num">${s.t?.slice(5,16).replace("T"," ")}</span>
        <${m} name=${s.kind==="note"?"file-text":Ce(s.type)} size=${14} />
        <span>${s.run?a`<a href=${se(s.run)}>${s.run.slice(-8)}</a> `:null}${s.description??s.type}</span></div>`)}
  </div>`}var Ie=["failed","killed","lost"];function De(e){let t=le(e.path),n=t==="."?e.path:e.path.slice(t.length+1),s=R(e.path)?[]:n.split("/"),o=s.length&&Se(s[s.length-1])?s[s.length-1]:null,r=s.slice(0,-1),l=i=>[...t==="."?[]:[t],...r.slice(0,i+1)].join("/");return a`<header class="header">
    <nav class="crumbs" aria-label="Breadcrumb">
      ${s.length?a`<a href=${$(t)}>${t==="."?"local":t}</a>`:null}
      ${r.map((i,p)=>a`<span class="sep">/</span><a href=${$(l(p))}>${i}</a>`)}
    </nav>
    ${o?a`<${tn} id=${o} scope=${e.path} />`:a`<${en} path=${e.path} />`}
    ${e.finding?a`<p class="finding">${e.finding}</p>`:null}
  </header>`}function en({path:e}){let t=C(h(nt(e)).data)[0]??null,n=h(t?.proposal?st(e):null).data,s=h(t?.proposal?at(e):null).data,o=s?.proposal?.rationale,r=s?.versions?.find(u=>u.version===s.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,l=e==="."?"local":e.split("/").pop();if(!t)return a`<h1 class="title" tabindex="-1">${l}</h1><div class="skeleton late" style="block-size: 52px"></div>`;let[i,p]=ht(n?.progress?.text??t.progress),d=Ie.reduce((u,v)=>u+(t[v]??0),0);return a`
    <h1 class="title" tabindex="-1">${l} <${w} spec=${k("research",t.status)} word /></h1>
    ${t.proposal?a`<div class="statement">
          <${Te} value=${t.proposal} label="the proposal's statement" locked=${s?r:"Loading the proposal\u2026"}
            render=${u=>a`<span data-tip=${r?void 0:o}>${u}</span>`}
            onSave=${u=>We(e,u)} />
        </div>`:null}
    ${t.proposal?a`<div class="preds">
          ${(n?.predictions??[]).map(u=>a`<span class="pred" key=${u.name} data-tip=${mt(u)}>
              <${w} spec=${k("result",u.result)} /><b>${u.name}</b></span>`)}
          ${n?.provisional?a`<span class="tag tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
          ${i?a`<span class="pred"><${Ge} fraction=${n?.progress?.fraction??null} label=${p??i} />
                <span data-tip=${p}>${i}</span></span>`:null}
          ${t.verdict?a`<span class="pred"><${w} spec=${k("verdict",t.verdict)} word /></span>`:null}
        </div>`:null}
    <div class="facts">
      <span class="fact"><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?a`<span class="fact"><${w} spec=${k("run","running")} /><b>${t.running}</b> running</span>`:null}
      ${t.finished?a`<span class="fact"><${w} spec=${k("run","finished")} /><b>${t.finished}</b> finished</span>`:null}
      ${d?a`<span class="fact tone-bad" data-tip=${Ie.filter(u=>t[u]).map(u=>`${t[u]} ${u}`).join(", ")}>
            <${m} name="circle-x" size=${15} /><b class="tone-bad">${d}</b> ${d===1?Ie.find(u=>t[u]):"ended early"}</span>`:null}
      ${t.notes?a`<span class="fact"><${m} name="file-text" size=${15} /><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${Tt} path=${e} />
    </div>`}function tn({id:e,scope:t}){let n=h(he(e,t)).data;if(!n)return a`<h1 class="title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 52px"></div>`;let s=n.run,o=()=>{navigator.clipboard?.writeText(s.id)};return a`
    <h1 class="title" tabindex="-1"><${Te} value=${s.name??s.id} label="the run's name" class="title-edit"
        onSave=${r=>Xe(s.id,t,r.trim())} />
      <${w} spec=${k("run",s.status)} word /></h1>
    ${s.error?a`<p class="statement bad-text" data-tip=${s.error}>${s.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span class="fact"><b>${ce(s.steps)}</b> steps</span>
      <span class="fact"><b>${de(s.duration_s)}</b></span>
      <span class="fact" data-tip=${s.created_at}>${_(s.created_at)}</span>
      <${Tt} path=${t} />
      <span class="fact">
        <${j} icon="copy" label=${`Copy the run id ${s.id}`} onClick=${o} />
        <${qe} icon="ellipsis" label="Details" title="Run details" class="run-details">
          <table class="kv">${nn(s).map(([r,l])=>a`<tr><td class="muted">${r}</td><td>${l}</td></tr>`)}</table>
          <div class="menu-list">
            <button type="button" onClick=${()=>S($(t,{run:s.id}),{replace:!0})}>
              <${m} name="panel-right" size=${15} /> Open in the side panel</button>
            <button type="button" onClick=${o}><${m} name="copy" size=${15} /> Copy the run id</button>
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
        </div>`:null}`}function Tt({path:e}){let t=h(tt(e)).data?.summary;if(!t)return null;let n=Object.entries(t.config??{}).map(([o,r])=>`${o} ${U(r)}`).join(", "),s=Se(e.split("/").pop()??"");return a`<span class="fact" data-tip=${`${t.stat} of ${t.metric} over ${s?"the run":"all runs"}`}>
    best <b>${t.metric} ${U(t.value)}</b>
    ${s?null:a`<span>· <a href=${se(t.run)}>${t.name}</a>${n?a` <em>(${n})</em>`:null}</span>`}
  </span>`}function nn(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,s])=>[n,String(s)])}function Ct(e,t){let n=e.split(`
`),s=t.split(`
`),o=n.length,r=s.length,l=Array.from({length:o+1},()=>new Uint32Array(r+1));for(let u=o-1;u>=0;u--)for(let v=r-1;v>=0;v--)l[u][v]=n[u]===s[v]?l[u+1][v+1]+1:Math.max(l[u+1][v],l[u][v+1]);let i=[],p=0,d=0;for(;p<o&&d<r;)n[p]===s[d]?(i.push({kind:"same",text:n[p]}),p++,d++):l[p+1][d]>=l[p][d+1]?i.push({kind:"removed",text:n[p++]}):i.push({kind:"added",text:s[d++]});for(;p<o;)i.push({kind:"removed",text:n[p++]});for(;d<r;)i.push({kind:"added",text:s[d++]});return i}function Lt(e,t=3){let n=[],s=0;for(;s<e.length;){if(e[s].kind!=="same"){n.push(e[s++]);continue}let o=s;for(;o<e.length&&e[o].kind==="same";)o++;let r=s===0?0:t,l=o===e.length?0:t;o-s>r+l+1?n.push(...e.slice(s,s+r),{kind:"skip",count:o-s-r-l},...e.slice(o-l,o)):n.push(...e.slice(s,o)),s=o}return n}function ye(e){let t=h($e(e.path)),n=X(),s=C(t.data),o=Q(()=>me(s.map(i=>i["run.id"]),n),[t.data,n]),r=Q(()=>new Map(s.map(i=>[i["run.id"],i["run.name"]??i["run.id"]])),[t.data]);if(!e.view)return a`<div class="view"><div class="skeleton late" style="block-size: 320px"></div></div>`;let l={path:e.path,colors:o,names:r,metrics:e.view.metrics??{}};return a`<div class="view"><${pe.Provider} value=${l}><${ge} node=${e.view.view} /><//></div>`}function Mt(e){let t=e.view,n=g(L),s=n.page==="group"&&n.version,o=t.versions?a`<a href=${$(e.path,{history:!0})}><${m} name="history" size=${14} /> history (${t.versions})</a>`:null,r;switch(t.source){case"draft":r=a`draft <b>${t.draft}</b>`;break;case"view":r=a`${t.title?a`<em>${t.title}</em> · `:null}saved ${_(Re(t.version))} by ${t.author??"unknown"}`;break;default:r=a`the built-in view`}return a`<div class="view-source">
    <${m} name="layout" size=${14} /><span>${r}</span>
    ${s?a`<a href=${$(e.path)}>an older version · show the current one</a>`:null}
    ${o}
    ${t.outdated?.length&&!s?a`<${sn} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||s?null:a`<${an} path=${e.path} />
        <${rn} path=${e.path} view=${t} />`}
  </div>`}function sn(e){let[t,n]=y(null),s=e.outdated.map(r=>r.name).join(", ");return a`<button type="button" class="link small" onClick=${async()=>{n(null);try{await Je(e.path)}catch(r){n(r.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${s} exists; update re-pins this view to it (a new version)`}>
      <${m} name="update" size=${14} /> update ${s}</button>
    ${t?a`<span class="bad-text small">${t}</span>`:null}`}function an(e){let[t,n]=y(null);return a`<button type="button" class="link small" onClick=${async()=>{n(null);try{Qe.set(await Ye(e.path,null,""))}catch(o){n(o.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${m} name="file-text" size=${14} /> add text</button>
    ${t?a`<span class="bad-text small">${t}</span>`:null}`}function rn(e){let t=ft(e.path),n=vt(t),[s,o]=y(!1),[r,l]=y(e.view.title??""),[i,p]=y(e.view.finding??""),[d,u]=y(null),[v,f]=y(!1);if(!n&&!s)return null;let D=async b=>{b.preventDefault(),f(!0),u(null);try{let x={charts:t.charts,added:t.added,order:t.order,spans:t.spans};await ne("save_view",{path:e.path,prefs:x,title:r,finding:i}),gt(e.path,()=>({view:{},charts:{},added:[],order:{},spans:{}})),Ue(q=>["view","view_history","summary"].includes(q.method)&&q.scope===e.path),o(!1)}catch(x){u(x.message)}finally{f(!1)}};return s?a`<form class="save-form" onSubmit=${D}>
    <label class="field"><span class="field-label">Title</span>
      <input value=${r} onInput=${b=>l(b.target.value)} /></label>
    <label class="field"><span class="field-label">Finding</span>
      <input value=${i} placeholder="the key result in one sentence"
        onInput=${b=>p(b.target.value)} /></label>
    <div class="save-actions">
      <button type="submit" class="button primary" disabled=${v}>${v?"Saving\u2026":"Save as view"}</button>
      <button type="button" class="link small" onClick=${()=>o(!1)}>cancel</button>
      ${d?a`<span class="bad-text small">${d}</span>`:null}
    </div>
  </form>`:a`<button type="button" class="link small save-view" onClick=${()=>o(!0)}
        data-tip="Save your chart settings and added charts as this page's view, for everyone">
      <${m} name="save" size=${14} /> Save as view</button>`}function It(e){let t=h(dt(e.path)),n=t.data?.entries??[],[s,o]=y(null),r=s??n.slice(0,2).map(i=>i.version).reverse(),l=i=>{let p=r.includes(i)?r.filter(d=>d!==i):[...r,i].slice(-2);o(p.sort())};return t.status==="error"?a`<${H} kind="error">${t.error}<//>`:a`<section class="history">
    <h2 class="history-title"><${m} name="history" size=${18} /> View history</h2>
    ${t.data&&!n.length?a`<${H}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((i,p)=>a`<li key=${i.version} class=${r.includes(i.version)?"picked":""}>
          <label><input type="checkbox" checked=${r.includes(i.version)} onChange=${()=>l(i.version)} />
            <span class="num muted" data-tip=${i.version}>${_(i.time)}</span>
            <b>${i.title??"untitled"}</b><span class="muted">${i.author??""}</span>
            ${i.message?a`<span>${i.message}</span>`:null}</label>
          <a href=${p===0?$(e.path):$(e.path,{version:i.version})}
            onClick=${d=>{d.preventDefault(),S(p===0?$(e.path):$(e.path,{version:i.version}))}}>${p===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${r.length===2?a`<${on} path=${e.path} a=${r[0]} b=${r[1]} />`:null}
  </section>`}function on(e){let t=i=>({method:"view_show",params:{group:e.path,version:i},scope:e.path}),n=h(t(e.a)).data,s=h(t(e.b)).data,o=h(V(e.path,e.a)).data,r=h(V(e.path,e.b)).data,l=n&&s?Lt(Ct(n.yaml,s.yaml)):[];return a`<div class="compare">
    <h3 class="block-title">Changes from ${_(Re(e.a))} to ${_(Re(e.b))}</h3>
    <pre class="diff">${l.map(i=>i.kind==="skip"?a`<div class="diff-skip">⋯ ${i.count} unchanged lines</div>`:a`<div class=${`diff-${i.kind}`}>${i.kind==="added"?"+ ":i.kind==="removed"?"\u2212 ":"  "}${i.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title">${o?.title??e.a}</h3><${ye} path=${e.path} view=${o} /></div>
      <div><h3 class="block-title">${r?.title??e.b}</h3><${ye} path=${e.path} view=${r} /></div>
    </div>
  </div>`}function Re(e){return e?`${e.slice(0,4)}-${e.slice(4,6)}-${e.slice(6,8)}T${e.slice(9,11)}:${e.slice(11,13)}:${e.slice(13,15)}Z`:null}function Dt(e){return E(()=>{document.title=`${e.path==="."?"local":e.path} \xB7 Beamtime`},[e.path]),e.history?a`<div class="page"><${De} path=${e.path} /><${It} path=${e.path} /></div>`:a`<div class="page">
    <${ln} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function ln(e){let t=h(V(e.path,e.version,e.draft));return E(()=>{t.status==="ready"&&requestAnimationFrame(Ke)},[t.status==="ready"]),a`
    <${De} path=${e.path} finding=${t.data?.finding} />
    ${t.data?a`<${Mt} path=${e.path} view=${t.data} />`:null}
    ${t.status==="error"?cn(e.path,t.error)?a`<${H} kind="warning">${t.error} The page fills in once the remote answers again.<//>`:a`<${H} kind="error">${t.error}<//>`:a`<${ye} path=${e.path} view=${t.data} />`}`}function cn(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function Rt(e){E(()=>{ie(V(e.id)).then(n=>S($(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=h(V(e.id));return t.status==="error"?a`<div class="page"><${H} kind="error">${t.error}<//></div>`:a`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}function Nt(){let e=g(Le),t=O(null);if(E(()=>{let o=t.current;if(!o||!e)return;o.showModal();let r=()=>Le.set(null);return o.addEventListener("close",r),()=>o.removeEventListener("close",r)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},s=String(n.props.title??n.props.y??"Chart");return a`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${s} closedby="any">
    <${pe.Provider} value=${e.view}><${ge} node=${n} /><//>
  </dialog>`}function zt(e,t){let n=e.toLowerCase(),s=t.toLowerCase();if(!n)return 1;let o=s.indexOf(n);if(o>=0)return 100-Math.min(o,50)-s.length/100;let r=0,l=0;for(let i of s)if(i===n[r]?r++:r>0&&l++,r===n.length)return 40-Math.min(l,39);return 0}function Ht(e){let[t,n]=y(e.query),[s,o]=y(0),r=O(null),l=C(h(K()).data),i=C(h(fe()).data);E(()=>{let c=r.current;c.showModal();let N=()=>I.set(null);c.addEventListener("close",N);let F=!1,re=A=>{let oe=c.getBoundingClientRect();return A.clientX<oe.left||A.clientX>oe.right||A.clientY<oe.top||A.clientY>oe.bottom},ze=A=>F=re(A),_e=A=>F&&re(A)&&c.close();return"closedBy"in HTMLDialogElement.prototype||(c.addEventListener("pointerdown",ze),c.addEventListener("pointerup",_e)),()=>{c.removeEventListener("close",N),c.removeEventListener("pointerdown",ze),c.removeEventListener("pointerup",_e)}},[]);let p=()=>r.current?.close(),d=c=>()=>S(c),u=L.value,v=u.page==="group"?u.path:".",f=(c,N,F,re)=>({section:"Commands",label:c,detail:N,sym:{icon:F,tone:"muted",label:c},run:re}),b=[...l.map(c=>({section:"Groups",label:c.path==="."?"local":c.path,detail:`${c.runs} runs${c.proposal?` \xB7 ${c.proposal}`:""}`,sym:k("research",c.status),run:d($(c.path))})),...i.map(c=>({section:"Runs",label:c["run.name"]??c["run.id"],detail:`${c["run.status"]} \xB7 ${c["run.path"]}`,sym:k("run",c["run.status"]),run:d($(c["run.path"]))})),f("Theme: light","","sun",()=>ue("light")),f("Theme: dark","","moon",()=>ue("dark")),f("Theme: follow the system","","monitor",()=>ue("system")),f("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),f("Show notes and timeline","i","file-text",d($(v,{drawer:!0}))),f("Show or hide the sidebar","\u2318B","panel-left",()=>M.set(!M.value)),f(z.value?"Resume live updates":"Pause live updates","p",z.value?"play":"pause",()=>z.set(!z.value)),f("Keyboard shortcuts","?","keyboard",()=>P.set(!0)),f("Settings","","settings",d("/settings/appearance"))].map(c=>({it:c,s:Math.max(zt(t,c.label),zt(t,c.detail)*.5)})).filter(c=>c.s>0).sort((c,N)=>N.s-c.s||_t(c.it.section)-_t(N.it.section)).slice(0,60).map(c=>c.it),x=c=>{c&&(p(),c.run())},q=c=>{if(c.key==="ArrowDown")o(Math.min(b.length-1,s+1));else if(c.key==="ArrowUp")o(Math.max(0,s-1));else if(c.key==="Enter")x(b[s]);else return;c.preventDefault()},Ne="";return a`<dialog class="sheet" ref=${r} aria-label="Search" closedby="any">
    <div class="palette-input"><${m} name="search" size=${18} />
      <input autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${b[s]?`pal-${s}`:void 0}
        onInput=${c=>{n(c.target.value),o(0)}} onKeyDown=${q} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${b.map((c,N)=>{let F=c.section!==Ne&&!t?Ne=c.section:null;return a`${F?a`<li class="section" role="presentation">${F}</li>`:null}
          <li id=${`pal-${N}`} class="item" role="option" aria-selected=${N===s}
              onMouseMove=${()=>o(N)} onClick=${()=>x(c)}>
            <${w} spec=${c.sym} /><span class="label">${c.label}</span><span class="detail">${c.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function _t(e){return["Groups","Runs","Commands"].indexOf(e)}function we(e,t=[]){let n=new Map,s=(r,l={})=>({path:r,name:r==="."?"local":r.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let r of e)n.set(r.path,s(r.path,r));n.has(".")||n.set(".",s("."));for(let r of t)r.name!=="local"&&(n.has(r.name)||n.set(r.name,s(r.name)),Object.assign(n.get(r.name),{state:r.state,error:r.error}));for(let r of n.values()){if(R(r.path))continue;let l=r.path.lastIndexOf("/"),i=l<0?".":r.path.slice(0,l);(n.get(i)??n.get(le(r.path))??n.get(".")).children.push(r)}for(let r of n.values())r.children.sort((l,i)=>l.name.localeCompare(i.name));let o=[...n.values()].filter(r=>r.path!=="."&&R(r.path)).sort((r,l)=>r.name.localeCompare(l.name));return[n.get("."),...o]}function Ot(e,t,n){let s=[],o=n.toLowerCase(),r=l=>{(!o||l.path.toLowerCase().includes(o)||Bt(l,o))&&(s.push(l),(o||t.has(l.path)||R(l.path))&&l.children.forEach(r))};return e.forEach(r),s}function Bt(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||Bt(n,t))}function Pt(e,t){if(R(t))return e;let n=t.lastIndexOf("/"),s=n<0?".":t.slice(0,n),o=r=>r.path===s?r:r.children.map(o).find(l=>l)??null;return e.map(o).find(r=>r)?.children??[]}function At(e){return R(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function Ut(){let e=g(L),t=h(K()),[n,s]=y(()=>new Set(ee("open",[]))),[o,r]=y(""),l=O(null),i=e.page==="group"?e.path:null,p=we(C(t.data),t.data?.meta?.sources??[]),d=Ot(p,pn(n,i),o),u=(f,D)=>{let b=new Set(n);D??!b.has(f)?b.add(f):b.delete(f),te("open",[...b]),s(b)};return a`<nav class="sidebar" aria-label="Groups">
    <label class="filter"><${m} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${o} aria-label="Filter groups"
        onInput=${f=>r(f.target.value)} />
    </label>
    <div class="tree" ref=${l} onKeyDown=${f=>{let D=[...l.current?.querySelectorAll("a.tree-item")??[]],b=D.indexOf(document.activeElement),x=d[b];switch(f.key){case"ArrowDown":D[Math.min(D.length-1,b+1)]?.focus();break;case"ArrowUp":D[Math.max(0,b-1)]?.focus();break;case"ArrowRight":x?.children.length&&u(x.path,!0);break;case"ArrowLeft":x&&n.has(x.path)?u(x.path,!1):x&&D[d.findIndex(q=>q.path===un(x.path))]?.focus();break;default:return}f.preventDefault()}} role="tree">
      ${d.map(f=>a`<${dn} key=${f.path} node=${f} current=${f.path===i}
        open=${n.has(f.path)||!!o} onToggle=${()=>u(f.path)} />`)}
    </div>
  </nav>`}function dn(e){let t=e.node,n=()=>ct(t.path),s=t.children.length>0&&!R(t.path);return a`<a class=${`tree-item${e.current?" current":""}${t.path.startsWith("@")&&R(t.path)?" source-root":""}`} href=${$(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${s?e.open:void 0}
      style=${`padding-inline-start:${6+At(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${o=>{o.metaKey||o.ctrlKey||(o.preventDefault(),S($(t.path)))}}>
    <span class="twisty" onClick=${o=>{o.preventDefault(),o.stopPropagation(),e.onToggle()}}>
      ${s?a`<${m} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    <span class="tree-name">${t.name}</span>
    ${t.state==="unreachable"?a`<${w} spec=${{icon:"cloud-off",tone:"muted",label:`Unreachable: ${t.error??"no answer"}`}} size=${13} />`:null}
    <span class="tree-marks">
      ${t.running?a`<${w} spec=${k("run","running")} size=${13} />`:null}
      ${t.failed?a`<${w} spec=${{...k("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${13} />`:null}
    </span>
    <span class="count">${t.runs||""}</span>
  </a>`}function un(e){if(R(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function pn(e,t){if(!t||t===".")return e;let n=new Set(e),s=t.split("/");for(let o=1;o<s.length;o++)n.add(s.slice(0,o).join("/"));return n}function Kt(){let e=g(L),t=g(M),n=g(I),s=g(P),o=O(null);E(()=>je(()=>o.current),[]),E(()=>(addEventListener("keydown",jt),()=>removeEventListener("keydown",jt)),[]);let r=e.page==="group"&&e.drawer,l;switch(e.page){case"group":l=a`<${Dt} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":l=a`<${Rt} id=${e.id} />`;break;case"settings":l=a`<${wt} />`;break;case"timeline":l=a`<${ut} key=${e.from} from=${e.from} />`;break;default:l=a`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return W?a`<main class="main render-main" ref=${o}>${l}</main>`:a`<div class=${`shell${t?"":" no-sidebar"}${r?" with-drawer":""}`}>
    <${xt} />
    ${t?a`<${Ut} />`:null}
    <main class="main" ref=${o}>${l}</main>
    ${r?a`<${Et} path=${e.path} run=${e.run} />`:null}
    <${St} />
    ${n!==null?a`<${Ht} query=${n} />`:null}
    ${s?a`<${hn} />`:null}
    <${Nt} />
  </div>`}function jt(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),I.set(I.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),M.set(!M.value);return}if(e.key==="Escape"){if(I.value!==null||P.value)return;let s=L.value;return s.page==="group"&&s.run?S($(s.path,{drawer:!0}),{replace:!0}):s.page==="group"&&s.drawer?S($(s.path),{replace:!0}):void 0}if(t||e.altKey||yt(e)||I.value!==null||P.value)return;let n=L.value;switch(e.key){case"/":e.preventDefault(),I.set("");break;case"?":P.set(!P.value);break;case"p":z.set(!z.value);break;case"i":n.page==="group"&&S($(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":M.set(!M.value);break;case"[":case"]":n.page==="group"&&mn(n.path,e.key==="]"?1:-1);break}}async function mn(e,t){let n=await ie(K()),s=Pt(we(C(n),n?.meta?.sources??[]),e),o=s.findIndex(l=>l.path===e),r=s[o+t];r&&S($(r.path))}function hn(){let e=O(null);return E(()=>{let t=e.current;t.showModal();let n=()=>P.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),a`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${ve.map(([t,n])=>a`<tr><td><kbd>${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 14px"><button class="link" autofocus>Close</button></form>
    </div>
  </dialog>`}var T=null,J=null,ke,ae;function Gt(){T=document.createElement("div"),T.className="bt-hint",T.setAttribute("popover","manual"),T.id="bt-hint",document.body.append(T),T.addEventListener("pointerenter",()=>clearTimeout(ae)),T.addEventListener("pointerleave",()=>Vt()),document.addEventListener("pointerover",e=>{let t=e.target.closest?.("[data-tip]");t&&t!==J&&(clearTimeout(ke),ke=setTimeout(()=>Ft(t),J?0:350))}),document.addEventListener("pointerout",e=>{let t=e.target.closest?.("[data-tip]");t&&(clearTimeout(ke),t===J&&Vt())}),document.addEventListener("focusin",e=>{let t=e.target.closest?.("[data-tip]");t&&e.target.matches(":focus-visible")&&Ft(t)}),document.addEventListener("focusout",()=>xe()),document.addEventListener("keydown",e=>{e.key==="Escape"&&J&&xe()}),document.addEventListener("pointerdown",()=>xe(),!0)}function Ft(e){let t=e.getAttribute("data-tip");if(!T||!t||!e.isConnected)return;clearTimeout(ae),J=e,T.textContent=t,T.matches(":popover-open")||T.showPopover();let n=e.getBoundingClientRect(),s=T.getBoundingClientRect(),o=6,r=n.top-s.height-o,l=r>=4?r:n.bottom+o,i=Math.min(Math.max(4,n.left+n.width/2-s.width/2),innerWidth-s.width-4);T.style.top=`${l}px`,T.style.left=`${i}px`}function Vt(){clearTimeout(ae),ae=setTimeout(xe,120)}function xe(){clearTimeout(ke),clearTimeout(ae),J=null,T?.matches(":popover-open")&&T.hidePopover()}Fe();if(W){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(B.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Oe.n}Gt();var $n=ne("meta").then(e=>(W&&(e={...e,settings:{...e.settings,theme_mode:B.value}}),be(e),e));W||Ae(async()=>{let[e,t]=await Promise.all([$n,ne("meta")]);e.bundle!==t.bundle?location.reload():be(t)});He(a`<${Kt} />`,document.getElementById("app"));
