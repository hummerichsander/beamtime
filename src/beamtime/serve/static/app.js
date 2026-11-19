import{$ as ot,$a as An,A as an,Aa as yn,B as De,Ba as qe,C as ie,Ca as lt,D as S,Da as Mt,E as tt,F as re,Fa as wn,G as ye,H as Ee,I as G,Ia as kn,J as B,K as ln,La as xn,M as N,Ma as Cn,N as cn,Na as Sn,O as dn,Oa as Nn,P as pe,Pa as Dn,Q as Ue,Qa as Rn,R as un,Ra as Pn,S as nt,T as Te,Ta as _n,U as $e,V as fn,Va as Ln,W as Et,Wa as In,X as st,Xa as On,Y as H,Ya as zn,Z as Y,Za as Bn,_ as de,_a as Hn,a as s,aa as hn,b as Yt,c as He,ca as Re,d as oe,da as Pe,e as et,fa as gn,ga as vn,h as Jt,ha as k,i as Zt,ia as _,j as Ae,ja as rt,k as Qt,ka as Q,l as en,la as z,m as tn,ma as D,na as We,oa as W,pa as we,q as F,qa as I,r as Ke,ra as ee,s as Ne,sa as je,t as St,ta as Ge,u as w,ua as at,v as nn,va as it,w as ae,wa as R,x as sn,xa as Ve,y as on,ya as Tt,z as rn,za as bn}from"./chunks/chunk-NXB7PTB7.js";import{a as qt,b as Xt}from"./chunks/chunk-O2K4N3UR.js";import{A as U,B as Be,J as mn,L as Fe,P as pn,Q as $n,U as En,Z as Tn,_ as Mn,b as jt,d as Gt,f as y,g as M,h as Vt,i as L,j as ze,k as q,n as xe,o as E,p as ve,q as me,t as X,u as Ct,w as be,x as Ce,y as Se,z as Qe}from"./chunks/chunk-WGYQC73K.js";import"./chunks/chunk-VC46IEJQ.js";function Me(e,t){De(n=>t.includes(n.method)&&n.scope!==null&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var Nt=["notes","timeline","groups","check","card","memory_show","status"];async function ct(e,t){let n=e.meta??{};await F("note_add",{group:e.group,type:t.type??e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),Me(e.group,Nt)}async function Kn(e,t,n,o){await F("note_add",{group:e,type:t,description:n,body:o}),Me(e,Nt)}async function Un(e,t){await F("memory_update",{group:e,body:t}),Me(e,["memory_show","status"])}async function Fn(e,t){let n=await F("proposal_show",{group:e}),o=Object.fromEntries(Object.entries(n.proposal??{}).filter(([r])=>!["schema","author","user","supersedes"].includes(r)));await F("proposal_set",{group:e,proposal:{...o,statement:t}}),Me(e,["groups","proposal_show","check","summary"])}async function Wn(e){await F("note_rm",{note:e.id}),Me(e.group,Nt)}async function jn(e,t,n){await F("name",{run:e,name:n}),Me(t,["card","runs","groups","summary","series"])}async function Dt(e,t){await F("run_promote",{runs:[ye(e,t)]}),Me(t,["card","runs","groups","summary","series","keys","check","proposal_show","status"])}async function dt(e,t,n){let o=await F("view_text",{path:e,id:t,text:n});return De(r=>["view","view_history"].includes(r.method)&&r.scope===e),o.id}async function Gn(e){await F("view_upgrade",{group:e}),De(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var _e=new xe(null);async function Vn(e,t){return await F("set",{key:e,value:t}),F("meta")}var ue=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),fe=(e,t=null,n=null,o=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{},...o?{metrics:o}:{}},scope:e}),Rt=(e,t=null)=>({method:"summary",params:{path:e,...t?{metrics:t}:{}},scope:e}),Le=e=>({method:"groups",params:{from:e,depth:0},scope:e}),qn=e=>({method:"check",params:{group:e},scope:e}),Xn=e=>({method:"proposal_show",params:{group:e},scope:e}),Ie=(e,t)=>({method:"card",params:{run:ye(e,t)},scope:t}),Yn=(e,t)=>({method:"output",params:{run:ye(e,t),tail:30},scope:t}),Jn=(e,t)=>({method:"run_diff",params:{run:ye(e,t)},scope:t}),Xe=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),Zn=e=>({method:"runs",params:{from:e,hidden:!0,where:{"run.hidden":!0},select:["run.name","run.status","run.created_at"],limit:200},scope:e}),ut=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),Qn=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),es=()=>({method:"status",params:{},scope:"."}),mt=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function Ye(e){let t=He(e).value.main;for(let n of[fe(e,null,null,t),Le(e),Xe(e),Rt(e,t)])St(n);Ne(fe(e,null,null,t)).then(n=>{for(let o of ts(n.view))St(o)}).catch(()=>{})}function ts(e){return e?[...oo.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(ts)]:[]}var oo=new Set(["line","custom"]),ns=e=>({method:"view_history",params:{group:e},scope:e});var $t="/static/favicon.svg",pt=null;async function ro(){if(pt)return pt;let e=new Image;e.src=$t,await e.decode();let t=32,n=document.createElement("canvas");n.width=n.height=t;let o=n.getContext("2d");if(!o)return $t;let r=getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();return r?(o.drawImage(e,0,0,t,t),o.beginPath(),o.arc(t-6,t-6,6,0,Math.PI*2),o.fillStyle=r,o.fill(),pt=n.toDataURL("image/png"),pt):$t}function ao(e){if(!1)return;let t=document.querySelector("link[rel=icon]");if(t instanceof HTMLLinkElement){if(!e){t.type="image/svg+xml",t.href=$t;return}ro().then(n=>{t.type="image/png",t.href=n})}}function Je(e,t=0){M(()=>{document.title=`${t?`(${t}) `:""}${e} \xB7 Beamtime`,ao(t>0)},[e,t])}function ss(e){let t=ie(e.split("/").pop()??""),n=w(t?null:Le(e)),o=w(t?Ie(e.split("/").pop()??"",e):null),r=t?o.data?.run.name??o.data?.run.id??e:e==="."?"local":e.split("/").pop()??e,i=t?o.data?.run.status==="running"?1:0:D(n.data)[0]?.running??0;Je(r,i)}var te=new xe(ve("sidebar",!0)),ne=new xe(null),he=new xe(!1),ge=new xe(null);te.subscribe(e=>me("sidebar",e));var os=ve("visit",Date.now());me("visit",Date.now());function rs(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var ft=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var io=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function ht(e){ge.set(e),rn(e.stale),nt.set(e.theme),Fe.set(e.colormaps),e.settings?.theme_mode&&$e.set(e.settings.theme_mode),Et()}var as=0;async function Pt(e,t){let n=++as;e==="theme_mode"&&($e.set(t),Et());let o=await Vn(e,t);n===as&&ht(o)}function is(){let e=E($e),t=de(),n=E(ge),[o,r]=y(null);Je("Settings");let i=(c,d)=>{r(null),Pt(c,d).catch(g=>r(g.message))},l=n?.settings??{},a=(c,d,g)=>s`
    <label class="field-label small" for=${`setting-${c}`}>${d}</label>
    <span class="input body">
      <select id=${`setting-${c}`} value=${l[c]} onChange=${m=>i(c,m.target.value)}>
        ${g.map(m=>s`<option value=${m}>${m}</option>`)}
      </select>
    </span>`;return s`<div class="page settings"><div class="sections">
    <${I} label="settings">
      <h1 class="page-title title" tabindex="-1">Settings</h1>
      <p class="muted small">Changes are written to <code>${l.file??"beamtime.yaml"}</code>, the project's settings.</p>
      ${o?s`<${z} kind="error">${o}<//>`:null}
    <//>
    <${I} label="appearance">
      <div class="settings-rows">
        <span class="field-label small">Mode</span>
        <div class="segmented" role="radiogroup" aria-label="Theme mode">
          ${io.map(([c,d,g])=>s`<button type="button" role="radio" aria-checked=${e===c} onClick=${()=>i("theme_mode",c)}>
            <${k} name=${d} size=${15} />${g}</button>`)}
        </div>
        ${a("theme","Theme",n?.themes??[])}
      </div>
      <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files recolor this layout: they go in <code>themes/</code> next to
        beamtime.yaml. Colormaps are chosen in each chart's settings.</p>
      ${(n?.theme?.problems??[]).map(c=>s`<${z} kind="warning">${c}<//>`)}
    <//>
    <${I} label="figures">
      <div class="settings-rows">
        <span class="field-label small">Style sheets</span>
        ${(n?.figure_styles??[]).length?s`<${it} options=${n.figure_styles} value=${l.figure_style??[]} label="Style sheets"
              placeholder="Add a style" onChange=${c=>i("figure_style",c)} />`:s`<span class="muted small"><code>${JSON.stringify(l.figure_style??[])}</code>; choosing others needs the figures
              extra: <code>uv add matplotlib scienceplots</code></span>`}
      </div>
      <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(l.figure_style??[])})</code>, in this order
        (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
        <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <//>
    <${I} label="keyboard">
      <table class="kv">${ft.map(([c,d])=>s`<tr><td><kbd class="small">${c}</kbd></td><td>${d}</td></tr>`)}</table>
    <//>
    <${I} label="about">
      <table class="kv">
        <tr><td class="muted">version</td><td>${n?.version}</td></tr>
        <tr><td class="muted">root</td><td><code class="code">${n?.root}</code></td></tr>
        ${(n?.sources??[]).map(c=>s`
          <tr><td class="muted">${c.name==="."?"local":c.name}</td><td><code class="code">${c.logdir}</code> (${c.kind}, ${c.state})</td></tr>`)}
      </table>
    <//>
  </div></div>`}var ls={system:"light",light:"dark",dark:"system"},lo={system:"monitor",light:"sun",dark:"moon"};function cs(){let e=E(ge),t=E($e),n=E(te);return s`<header class="topbar">
    <${W} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>te.set(!n)} />
    <a class="project heading" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>ne.set("")} aria-label="Search (⌘K)">
      <${k} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${co} />
      <${W} icon=${lo[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${ls[t]})`}
        onClick=${()=>{Pt("theme_mode",ls[t])}} />
      <a class="icon-button" href=${tt(B.value.page==="group"?B.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${k} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${k} name="settings" size=${16} /></a>
    </div>
  </header>`}function co(){let t=(w(ue()).data?.meta?.sources??[]).filter(n=>n.name!==".");return t.length?s`${[{name:".",state:"connected"},...t].map(n=>s`<a class=${`source small ${n.state}`}
      href=${S(n.name)}
      data-tip=${n.state==="connected"?`${n.name==="."?"local":n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${k} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name==="."?"local":n.name}</a>`)}`:s`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${k} name="server" size=${15} /> local</span>`}function uo(e){let[t,n]=y(Date.now());return M(()=>{let o=setInterval(()=>n(Date.now()),e);return()=>clearInterval(o)},[e]),t}function mo(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function ds(){let e=E(sn),t=E(ae),n=E(on),o=E(B),r=uo(5e3),i=w(es()).data,l=D(w(mt()).data),a=E(ge),c=i?.daemon,d=i?.runs?.running??0,g=l.filter(T=>T["run.status"]==="failed"&&mo(T["run.ended_at"])>os).length,m=i?.meta?.freshness,[p,$,v]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&c?["",`live \xB7 updated ${U(new Date(n).toISOString(),r)}`,`beamtime serve, pid ${c.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return s`<footer class="statusbar small">
    <span class="status-item" data-tip=${v}><span class=${`live-dot ${p}`}></span>${$}</span>
    ${d?s`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>ne.set("running")}>
          <${k} name="circle-dot" size=${14} class="tone-accent" />${d} running</button>`:null}
    ${g?s`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>ne.set("failed")}>
          <${k} name="circle-x" size=${14} />${g} failed since your last visit</button>`:null}
    ${m?.behind?s`<span class="status-item warn-text" data-tip=${m.text}><${k} name="hourglass" size=${14} />${m.behind} runs behind</span>`:null}
    ${m?.damaged?.length?s`<span class="status-item warn-text" data-tip=${m.damaged.join(`
`)}><${k} name="triangle-alert" size=${14} />${m.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${o.page==="group"&&o.run?s`<span class="status-item"><${k} name="activity" size=${14} />1 run selected</span>`:null}
    <${W} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>ae.set(!t)} />
    ${a?.outdated?s`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item">${a?.version?`beamtime ${a.version}`:""}</span>
  </footer>`}var us=null;function gt(e){let t=L(null),[n,o]=y(null),[r,i]=y(!1),[l,a]=y(!1);M(()=>{let m=!0;return us??=import("./chunks/md-SW3VT2BQ.js"),us.then(p=>p.render(e.text??"")).then(p=>m&&o(p)),()=>{m=!1}},[e.text]),Vt(()=>{let m=t.current;if(!m||!e.clamp)return;let p=()=>a(m.scrollHeight>m.clientHeight+2),$=new ResizeObserver(p);return $.observe(m),()=>$.disconnect()},[e.clamp,n]);let c=e.clamp&&!r,d=`md${c?" clamped":""}`,g=c?`--clamp:${e.clamp}`:"";return s`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?s`<div class=${d} ref=${t} style=${g}>
          ${(e.text??"").split(/\n{2,}/).map(m=>s`<p>${m}</p>`)}
        </div>`:s`<div class=${d} ref=${t} style=${g} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(l||r)?s`<button type="button" class="link small more" onClick=${()=>i(!r)}>${r?"less":"more"}</button>`:null}
  </div>`}function ke(e){let[t,n]=y(!!e.startEditing),[o,r]=y(e.value),[i,l]=y(null),[a,c]=y(null),d=L(null),g=L(!1);M(()=>l(null),[e.value]),M(()=>{!t||!d.current||(d.current.focus(),e.startEditing?d.current.select():d.current.setSelectionRange(d.current.value.length,d.current.value.length))},[t]);let[m,p]=y(!1),$=e.locked??void 0,v=h=>{if(!h.target.closest("a, button, input, summary")){if($)return p(!0);h.preventDefault(),r(i??e.value),c(null),g.current=!1,n(!0)}},T=()=>{g.current=!0,n(!1),c(null),e.onCancel?.()},f=async()=>{if(g.current)return;g.current=!0;let h=e.multiline?o.trim():o.replace(/\s*\n\s*/g," ").trim();if(h===e.value.trim()||!h&&!e.multiline)return T();n(!1),l(h);try{await e.onSave(h)}catch(b){l(null),r(h),c(b.message),g.current=!1,n(!0)}},x=h=>{if(h.key==="Escape")return h.preventDefault(),h.stopPropagation(),T();h.key!=="Enter"||h.isComposing||h.keyCode===229||(!e.multiline||h.metaKey||h.ctrlKey)&&(h.preventDefault(),f())};if(t)return s`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${d} class="edit-field" value=${o} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,o.split(`
`).length+1)):1}
        onInput=${h=>r(h.target.value)} onKeyDown=${x} onBlur=${f}></textarea>
      <span class="edit-hint small">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${a?s` · <span class="bad-text">${a}</span>`:null}</span>
    </div>`;let u=i??e.value;return s`<div class=${`editable${$?" locked":""}${i!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${$?`${e.label}: ${$}`:`Edit ${e.label}`}
      data-tip=${$} onClick=${v} onBlur=${()=>p(!1)}
      onKeyDown=${h=>h.key==="Enter"&&h.target===h.currentTarget&&v(h)}>
    ${u.trim()?e.render?e.render(u):u:s`<span class="muted">${e.placeholder??"Click to write"}</span>`}
    ${m&&$?s`<span class="edit-hint small locked-why" role="status"><${k} name="lock" size=${14} /> ${$}</span>`:null}
  </div>`}function _t(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function ms({node:e}){let t=Y("proposal"),n=Y("check"),o=t.data,r=n.data;if(!o)return s`<${Q} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let i=o.proposal??{},l=(o.versions??[]).filter(c=>c.version!==o.version),a=!e.props.of||e.props.of===".";return s`<${Q} title="Predictions" result=${t} class="proposal">
    ${a?null:s`<p class="statement">${i.statement}</p>`}
    ${i.rationale?s`<p class="rationale prose">${i.rationale}</p>`:null}
    <${yn} predictions=${r?.predictions} />
    ${l.length?s`<${Ge} summary=${`${l.length} earlier version${l.length>1?"s":""}`}>
          ${l.map(c=>s`<p class="small"><code>${c.version}</code> ${c.statement}
            <span class="muted">(${c.runs} runs, check ${c.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function ps({node:e}){let t=Y("main"),n=e.data?.main.params.group??".",o=t.data?.chain??[],r=o.find(a=>a.group===n)??null,i=o.filter(a=>a.group!==n),l=r?.notes_since?"out of date":r?`version ${r.versions??1}`:"none yet";return s`<${We} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?l:void 0} open=${!1} result=${t}
      action=${s`<${_} spec=${{icon:"circle-help",tone:"muted",label:$o}} />`}>
    <${ke} value=${r?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${a=>s`<${gt} text=${a} />`} onSave=${a=>Un(n,a)} />
    ${r&&(r.body?.length>(t.data?.budget??1/0)||r.notes_since>=po)?s`<p class="memory-meta small warn-text">${r.body?.length>t.data.budget?`${r.body.length} characters, beyond the budget of ${t.data.budget}`:`${r.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${r?s`<p class="memory-meta small">${r.author} · covers notes until ${r.covers_until?.slice(0,10)}
          ${r.notes_since?s` · <span class="warn-text">${r.notes_since} newer note${r.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${i.length?s`<p class="memory-meta small">Memory above this group: ${i.map((a,c)=>s`${c?", ":""}<a href=${S(a.group)}>${a.group==="."?"local":a.group}</a>`)}</p>`:null}
  <//>`}var po=5,$o="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",fo="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function $s({node:e}){let t=Y("main"),n=e.data?.main.params.from??".",o=D(t.data).filter(r=>r.path!==n);return s`<${Q} title=${e.props.title} count=${t.data?String(o.length):void 0} result=${t}>
    ${t.data&&!o.length?s`<${z}>No groups below.<//>`:null}
    <div class="group-list">
      ${o.map(r=>{let[i,l]=_t(r.progress),a=(r.failed??0)+(r.killed??0)+(r.lost??0);return s`<a class="group-row" key=${r.path} href=${S(r.path)}
            onPointerEnter=${()=>Ye(r.path)} onFocus=${()=>Ye(r.path)}>
          <${_} spec=${R("research",r.status)} />
          <span class="gname heading">${r.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${r.status!=="concluded"?s`<span class=${`tone-${R("research",r.status).tone}`}>${R("research",r.status).label}</span>`:null}
            ${r.check?s`<${_} spec=${R("result",r.check)} word />`:null}
            ${r.verdict?s`<${_} spec=${R("verdict",r.verdict)} />`:null}
            ${i?s`<span data-tip=${l}>${i}</span>`:null}
            <span class="num"><b>${r.runs}</b> runs</span>
            ${r.running?s`<${_} spec=${R("run","running")} />`:null}
            ${a?s`<span class="tone-bad num" data-tip="failed, killed or lost"><${k} name="circle-x" size=${14} /> ${a}</span>`:null}
          </span>
          ${r.proposal?s`<span class="gstatement caption">${r.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function fs({node:e}){let t=Y("main"),n=e.data?.main.params.from??".",[o,r]=y(!1),i=(t.data?.entries??[]).filter(a=>!String(a.state??"").startsWith("superseded")),l=t.data?.meta?.matched??i.length;return s`<${We} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(l):void 0} result=${t}
      action=${s`<${_} spec=${{icon:"circle-help",tone:"muted",label:fo}} />
        ${s`<${W} icon="plus" label="Add a note" onClick=${()=>r(!0)} />`}`}>
    <div class="notes">
      ${o?s`<${vo} group=${n} onDone=${()=>r(!1)} />`:null}
      ${t.data&&!i.length&&!o?s`<p class="muted small">No notes yet.</p>`:null}
      ${i.map(a=>s`<${vt} key=${a.id} note=${a} scope=${n} />`)}
      ${t.data?.more&&e.data?s`<${hs} call=${e.data.main} before=${i[i.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var ho=20;function hs(e){let[t,n]=y(!1),o=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:ho}}:null,r=w(o);if(!t)return s`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(r.status==="error")return s`<p class="bad-text small">${r.error}</p>`;let i=r.data?.entries??[];return s`${r.data?null:s`<div class="skeleton" style="block-size: 40px"></div>`}
    ${i.map(l=>s`<${vt} key=${l.id} note=${l} scope=${e.scope} />`)}
    ${r.data?.more?s`<${hs} call=${e.call} before=${i[i.length-1]?.id} scope=${e.scope} />`:null}`}var go=["observation","decision","idea","question","theory"];function gs(e){return(e?.note_types??go).filter(t=>t!=="verdict")}function vo(e){let t=gs(E(ge)),[n,o]=y("observation"),[r,i]=y(""),[l,a]=y(""),[c,d]=y(null),[g,m]=y(!1),p=async v=>{if(v.preventDefault(),!r.trim())return d("give the note a title");m(!0);try{await Kn(e.group,n,r.trim(),l.trim()),e.onDone()}catch(T){d(T.message),m(!1)}};return s`<form class="note new-note" onSubmit=${p} onKeyDown=${v=>{v.key==="Escape"&&e.onDone(),v.key==="Enter"&&(v.metaKey||v.ctrlKey)&&p(v)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${n} aria-label="Note type" onChange=${v=>o(v.target.value)}>
        ${t.map(v=>s`<option value=${v}>${v}</option>`)}
      </select></span>
      <span class="input body new-note-field"><input class="new-note-title" value=${r} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${v=>i(v.target.value)} /></span>
    </div>
    <span class="input small"><textarea class="new-note-body" rows="4" value=${l} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${v=>a(v.target.value)}></textarea></span>
    <div class="save-actions">
      <${ee} type="submit" icon=${g?"hourglass":"plus"} disabled=${g}>${g?"Adding\u2026":"Add note"}<//>
      <${ee} icon="x" kind="quiet" onClick=${e.onDone}>Cancel<//>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${c?s`<span class="bad-text small">${c}</span>`:null}
    </div>
  </form>`}function bo({note:e}){let t=gs(E(ge)).filter(n=>n!==e.type);return e.type==="verdict"?s`<span class="sym tone-accent" data-tip="a verdict's type can't change; write a new note">
      <${k} name=${R("note","verdict").icon} size=${15} /></span>`:s`<${at} icon=${R("note",e.type).icon} label="Change the note's type" title="Note type">
    <div class="menu-list">
      ${t.map(n=>s`<button type="button" key=${n} onClick=${()=>ct(e,{type:n})}>
        <${k} name=${R("note",n).icon} size=${15} /> ${n}</button>`)}
    </div>
  <//>`}function vt(e){let t=e.note,[n,o]=y(!!e.open),[r,i]=y(!1),l=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,a=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),c=t.meta?.author;return s`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${d=>!d.target.closest(".editable, a, .note-delete, .popover-wrap")&&o(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${k} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${bo} note=${t} />
      <${ke} value=${t.description} label="the note's title" class="note-title prose" render=${wo}
        onSave=${d=>ct(t,{description:d})} />
      ${t.overall?s`<${_} spec=${R("verdict",t.overall)} />`:null}
      ${t.state?s`<${we} tone="warn">${t.state}<//>`:null}
      ${l?s`<a class="note-group small" href=${S(l)} data-tip="from this group">${yo(l,e.scope)}</a>`:null}
      <span class="note-meta small">${c?`${c} \xB7 `:""}${U(a)}</span>
      ${s`<${W} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${r}
        onClick=${d=>{d.stopPropagation(),i(!r)}} />`}
    </div>
    ${r?s`<div class="note-confirm small" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <${ee} icon="trash" kind="danger" onClick=${()=>{Wn(t)}}>Delete<//>
          <${ee} icon="x" kind="quiet" onClick=${()=>i(!1)}>Cancel<//>
        </div>`:null}
    ${n?s`<${ke} value=${t.body??""} label="the note" multiline class="note-body prose markdown"
          placeholder="Add details in Markdown" render=${d=>s`<${gt} text=${d} />`}
          onSave=${d=>ct(t,{body:d})} />`:null}
  </article>`}function yo(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,o=n.split("/").pop()??n;return ie(o)?o.slice(-8):n}function vs({node:e}){let t=Y("main"),n=t.data?.lines??[],o=t.data?.meta??{},r=s`<${k} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${o.total_lines??n.length} lines${(o.shown??0)<(o.total_lines??0)?`, last ${o.shown}`:""}`:""}</span>`;return s`<${Q} result=${t}>
    <${Ge} summary=${r} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function bs({node:e}){let t=q(H);return s`<${Q} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${ke} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${_e.value===e.id} onCancel=${()=>_e.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>s`<${gt} text=${n} />`}
      onSave=${n=>(_e.set(null),dt(t.path,e.id,n))} />
  <//>`}function ys({node:e}){return s`<${z} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function wo(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let o=n.slice(2,-2),[r]=o.split(/[#@]/),i=r.split("/").pop()??"";return s`<a href=${ie(i)?re(i):S(r)}>${o}</a>`}return n.startsWith("`")?s`<code>${n.slice(1,-1)}</code>`:n})}function ko(e,t){let n=/^(?:ssh|https?|git):\/\/(?:[^@/]*@)?([^/:]+)(?::\d+)?\/(.+?)(?:\.git)?\/?$/.exec(e??""),o=/^(?:[^@/]+@)?([^/:]+):(?!\/)(.+?)(?:\.git)?\/?$/.exec(e??""),[,r,i]=n??o??[];return!r||!i?null:r==="github.com"?{host:"GitHub",url:`https://github.com/${i}/commit/${t}`}:r==="gitlab.com"||r.startsWith("gitlab.")?{host:"GitLab",url:`https://${r}/${i}/-/commit/${t}`}:null}function bt(e){let{git:t,copied_from:n}=e.run,o=[];return t?.commit&&o.push(["code",s`<${xo} git=${t} />`]),n&&o.push(["copied from",s`<a href=${re(n.id)} data-tip=${`${n.id}, ${n.at}`}>${n.path??n.id}</a>`]),e.checkpoints?.length&&o.push(["checkpoints",s`${e.checkpoints.map(r=>s`<${Co} key=${r.name} ck=${r} />`)}`]),o}function xo({git:e}){let t=ko(e.remote,e.commit);return s`<span>${e.commit.slice(0,10)}${e.branch?s` on ${e.branch}`:null}
    ${e.dirty?s` <${we} tone="warn" tip="Uncommitted changes when the run started">dirty<//>`:null}
    ${t?s` · <a href=${t.url} target="_blank" rel="noopener noreferrer">${t.host}</a>`:null}</span>`}function Co({ck:e}){let t=()=>{navigator.clipboard?.writeText(e.location)};return s`<div class="checkpoint">
    <span class=${e.exists?"":"muted"} data-tip=${e.location??void 0}>${e.name}</span>
    ${e.exists?null:s`<${we} tone="warn" tip=${e.location??void 0}>missing<//> <span class="muted">${So(e)}</span>`}
    ${e.location?s`<${W} icon="copy" label=${`Copy the path of ${e.name}`} onClick=${t} />`:null}
  </div>`}function So(e){return e.location?e.via==="origin"?"not found where the source run kept it":"not found at its recorded location":"no location recorded"}function yt({run:e,scope:t}){let[n,o]=y(!1),r=w(n?Jn(e,t):null);return s`<${Ge} summary="Uncommitted changes" onToggle=${o}>
    ${r.error?s`<p class="muted small">${r.error}</p>`:null}
    ${r.data?s`<pre class="log code diff">${String(r.data.text).split(`
`).map(i=>s`<span class=${Eo(i)}>${i}\n</span>`)}</pre>`:n&&!r.error?s`<div class="skeleton late" style="block-size: 80px"></div>`:null}
  <//>`}function Eo(e){return e.startsWith("+++")||e.startsWith("---")||e.startsWith("@@")?"muted":e.startsWith("+")?"tone-good":e.startsWith("-")?"tone-bad":""}function ws(e){let t=()=>N(S(e.path),{replace:!0});return s`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${k} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${W} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?s`<${To} id=${e.run} scope=${e.path} />`:s`<${Mo} path=${e.path} />`}
  </aside>`}function To({id:e,scope:t}){let n=w(Ie(e,t)).data,o=w(Yn(e,t)).data,r=w(Xe(t)).data,i=w({method:"keys",params:{from:t},scope:t}).data,l=de(),a=ze(()=>ot(D(r).map(p=>p["run.id"]),l).get(e),[r,l,e]);if(!n)return s`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let c=n.run,d=Object.entries(n.metrics??{}),g=mn(a,l),m=bt(n);return s`<div class="drawer-body">
    <h3 class="heading"><span class=${g.class} style=${g.style}></span>
      <a href=${re(e)}>${c.name}</a></h3>
    <p class="facts small">
      <${_} spec=${Ve(c.status,c.exit)} word tip=${Qe(c)} />
      <span><b>${Ce(c.steps)}</b> steps</span>
      <span><b>${Se(c.duration_s)}</b></span>
      <span data-tip=${c.created_at}>${U(c.created_at)}</span>
    </p>
    ${c.error?s`<pre class="log code bad-text">${c.error}</pre>`:null}
    ${m.length?s`<table class="kv small">${m.map(([p,$])=>s`<tr><td class="muted">${p}</td><td>${$}</td></tr>`)}</table>`:null}
    ${c.git?.dirty?s`<${yt} run=${c.id} scope=${t} />`:null}
    <h4 class="small">Config</h4>
    <${lt} config=${n.config??{}} varying=${qe(i)} />
    ${d.length?s`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${d.map(([p,$])=>s`<tr><td>${p}</td><td class="num"><b>${X($.last)}</b></td>
              <td class="num">${X($.min)}</td><td class="num">${X($.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?s`<h4 class="small">Cited by</h4>${n.cited_by.map(p=>s`<p class="small"><${_} spec=${R("note",p.type)} /> ${p.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(p=>s`<div class="event small"><span class="muted num">${p.t?.slice(5,16).replace("T"," ")}</span>
        <${k} name=${Tt(p.type)} size=${14} /><span>${p.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(o?.lines??[]).join(`
`)}</pre>
  </div>`}function Mo({path:e}){let t=w(ut(e)).data,n=w(Qn(e)).data;return s`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?s`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(o=>!String(o.state??"").startsWith("superseded")).map(o=>s`<${vt} key=${o.id} note=${o} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(o=>s`<div class="event small"><span class="muted num">${o.t?.slice(5,16).replace("T"," ")}</span>
        <${k} name=${o.kind==="note"?"file-text":Tt(o.type)} size=${14} />
        <span>${o.run?s`<a href=${re(o.run)}>${o.run.slice(-8)}</a> `:null}${o.description??o.type}</span></div>`)}
  </div>`}function wt(e,t){let n=w(e),o=L(null);return n.status!=="loading"&&(o.current={scope:t,result:n}),n.status==="loading"&&o.current?.scope===t?o.current.result:n}var Lt=null;function ks(e){Lt?.();let t=document.querySelector(".main");if(!e||!t)return;let n=e.getBoundingClientRect().top,o=new ResizeObserver(()=>{e.isConnected&&(t.scrollTop+=e.getBoundingClientRect().top-n)});for(let a of t.children)o.observe(a);let r=["wheel","touchmove","keydown","pointerdown"],i=()=>{o.disconnect(),clearTimeout(l);for(let a of r)removeEventListener(a,i);Lt=null},l=setTimeout(i,5e3);for(let a of r)addEventListener(a,i,{passive:!0});Lt=i}var It=["failed","killed","lost"],No={icon:"eye-off",tone:"muted",label:"Hidden"},Do="Hidden: left out of tables, counts and checks until promoted";function Ot(e){let t=Ee(e.path),n=t==="."?e.path:e.path.slice(t.length+1),o=G(e.path)?[]:n.split("/"),r=o.length&&ie(o[o.length-1])?o[o.length-1]:null,i=o.slice(0,-1),l=a=>[...t==="."?[]:[t],...i.slice(0,a+1)].join("/");return s`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${o.length?s`<a href=${S(t)}>${t==="."?"local":t}</a>`:null}
      ${i.map((a,c)=>s`<span>/</span><a href=${S(l(c))}>${a}</a>`)}
    </nav>
    ${r?s`<${_o} id=${r} scope=${e.path} />`:s`<${Ro} path=${e.path} />`}
    ${e.finding?s`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function Ro({path:e}){let t=D(w(Le(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return s`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let o=E(B),r=o.page==="group"&&o.hiddenRuns,i=Object.entries(w({method:"keys",params:{from:e},scope:e}).data?.codes??{}),l=It.reduce((a,c)=>a+(t[c]??0),0);return s`
    <h1 class="page-title title" tabindex="-1">${n} <${_} spec=${R("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?s`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?s`<span><b>${t.finished}</b> finished</span>`:null}
      ${l?s`<span class="tone-bad" data-tip=${It.filter(a=>t[a]).map(a=>`${t[a]} ${a}`).join(", ")}>
            <${k} name="circle-x" size=${15} /> <b>${l}</b> ${l===1?It.find(a=>t[a]):"ended early"}</span>`:null}
      ${i.length?s`<span data-tip=${i.map(([a,c])=>`${a}: ${c} run${c===1?"":"s"}`).join(", ")}>
            <${k} name="git-commit" size=${15} /> <b>${i.length}</b> code versions</span>`:null}
      ${t.hidden?s`<span><a href=${S(e,{hidden:!r})} data-tip=${r?"Close the list of hidden runs":"List the hidden runs"}>
            <${k} name="eye-off" size=${15} /> <b>${t.hidden}</b> hidden</a></span>`:null}
      ${t.notes?s`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${Ss} path=${e} />
    </p>`}function xs({path:e}){let t=D(w(Zn(e)).data);return t.length?s`<${I} label="hidden runs">
    <table class="runs">
      <thead><tr class="small"><th>run</th><th>status</th><th>created</th><th></th></tr></thead>
      <tbody>${t.map(n=>s`<tr key=${n["run.id"]}>
        <td><a href=${re(n["run.id"],e)}>${n["run.name"]??n["run.id"]}</a></td>
        <td><${_} spec=${Ve(n["run.status"],null)} word /></td>
        <td class="muted" data-tip=${n["run.created_at"]}>${U(n["run.created_at"])}</td>
        <td><${ee} icon="eye" kind="quiet" onClick=${()=>Dt(n["run.id"],e)}>Promote<//></td>
      </tr>`)}</tbody>
    </table>
  <//>`:null}function Cs({path:e}){let t=D(w(Le(e)).data)[0]??null,n=w(t?.proposal?qn(e):null).data,o=w(t?.proposal?Xn(e):null).data;if(!t?.proposal)return null;let r=o?.proposal?.rationale,i=o?.versions?.find(c=>c.version===o.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[l,a]=_t(n?.progress?.text??t.progress);return s`<${I} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${ke} value=${t.proposal} label="the proposal's statement" locked=${o?i:"Loading the proposal\u2026"}
          render=${c=>s`<span data-tip=${i?void 0:r}>${c}</span>`}
          onSave=${c=>Fn(e,c)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(c=>{let d=R("result",c.result),g=bn(c),m=g?`${d.label}: ${g}`:d.label;return s`<span class=${`check small tone-${d.tone}`} key=${c.name} data-tip=${m}
              aria-label=${`${c.name}: ${m}`} tabindex="0"><${k} name=${d.icon} size=${14} />${c.name}</span>`})}
        ${n?.provisional||l?s`<span class="small">
              ${n?.provisional?s`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${l?s`<span class="muted" data-tip=${a}>${n?.provisional?" \xB7 ":""}${l}</span>`:null}
            </span>`:null}
      </div>
      <${Po} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function Po(e){let t=w(e.verdict?ut(e.path):null).data;if(!e.verdict)return s`<p class="verdict-line muted">no verdict yet</p>`;let n=R("verdict",e.verdict),o=(t?.entries??[]).find(i=>i.type==="verdict"&&(i.group??e.path)===e.path),r=o?be(o.id):null;return s`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${k} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${o?s`<span class="small muted" data-tip=${r}>verdict${o.meta?.author?` by ${o.meta.author}`:""}${r?` \xB7 ${U(r)}`:""}</span>`:null}
  </p>`}function _o({id:e,scope:t}){let n=w(Ie(e,t)).data;if(!n)return s`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let o=n.run,r=()=>{navigator.clipboard?.writeText(o.id)},i=()=>{Dt(o.id,t)};return s`
    <h1 class="page-title title" tabindex="-1"><${ke} value=${o.name??o.id} label="the run's name" class="title-edit"
        onSave=${l=>jn(o.id,t,l.trim())} />
      <${_} spec=${Ve(o.status,o.exit)} word tip=${Qe(o)} />
      ${o.hidden?s`<${_} spec=${No} word tip=${Do} />`:null}</h1>
    ${o.error?s`<p class="bad-text" data-tip=${o.error}>${o.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${Ce(o.steps)}</b> steps</span>
      <span><b>${Se(o.duration_s)}</b></span>
      ${n.progress?s`<${Lo} run=${o} progress=${n.progress} />`:null}
      <span data-tip=${o.created_at}>${U(o.created_at)}</span>
      <${Ss} path=${t} />
      ${o.hidden?s`<${W} icon="eye" label="Promote: count this run in tables, charts and checks" onClick=${i} />`:null}
      <${W} icon="copy" label=${`Copy the run id ${o.id}`} onClick=${r} />
      <${at} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${[...Io(o),...bt(n)].map(([l,a])=>s`<tr><td class="muted">${l}</td><td>${a}</td></tr>`)}</table>
        ${o.git?.dirty?s`<${yt} run=${o.id} scope=${t} />`:null}
        <div class="menu-list">
          <button type="button" onClick=${()=>N(S(t,{run:o.id}),{replace:!0})}>
            <${k} name="panel-right" size=${15} /> Open in the side panel</button>
          ${o.hidden?s`<button type="button" onClick=${i}><${k} name="eye" size=${15} /> Promote</button>`:null}
          <button type="button" onClick=${r}><${k} name="copy" size=${15} /> Copy the run id</button>
          ${o.git?.commit?s`<button type="button" onClick=${()=>navigator.clipboard?.writeText(o.git.commit)}>
            <${k} name="git-commit" size=${15} /> Copy the commit</button>`:null}
        </div>
      <//>
    </div>
    ${(n.proposals??[]).length?s`<div class="checks">
          ${n.proposals.map(l=>{let a=R("result",l.check);return s`<a class=${`check small tone-${a.tone}`} href=${S(l.group)} data-tip=${l.statement}>
              <${k} name=${a.icon} size=${14} />${l.group==="."?"own proposal":l.group}
              ${l.verdict?s`<${_} spec=${R("verdict",l.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function Lo({run:e,progress:t}){let{epoch:n,total:o,fraction:r,steps_per_epoch:i}=t,l=e.status==="running"&&r!==null&&i&&e.steps_per_s?Se((1-r)*o*i/e.steps_per_s):null;return s`<span>epoch <b>${n}</b>${o?` of ${o}`:""}${r===null?"":` \xB7 ${Math.round(r*100)} % through`}${l?` \xB7 about ${l} left`:""}</span>`}function Ss({path:e}){let t=oe(e).main,n=wt(Rt(e,t),e).data?.summary;if(!n)return null;let o=Object.entries(n.config??{}).map(([l,a])=>`${Be(l)} ${X(a)}`).join(", "),r=ie(e.split("/").pop()??""),i=`${n.stat} of ${n.metric} over ${r?"the run":"all runs"}${o?` (${o})`:""}`;return s`<span data-tip=${i}>
    best <b>${n.label??Be(`metric.${n.metric}.${n.stat}`)} ${X(n.value)}</b>
    ${r?null:s` · <a href=${re(n.run)}>${n.name}</a>`}
  </span>`}function Io(e){return[["id",e.id],["host",e.host],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,o])=>[n,String(o)])}var zt=80;function Es({node:e}){let t=Y("main"),n=Y(e.data?.keys?"keys":""),o=e.props.mode==="run",r=e.props.title??(o?"Config":"Hyperparameters");return s`<${We} id=${`config:${e.id}`} title=${r} open=${e.props.open} result=${t}>
    ${t.data?o?s`<${lt} config=${t.data.config} varying=${qe(n.data)} />`:s`<${Oo} rows=${t.data.config?.rows??[]} />`:s`<div class="skeleton late" style="block-size: 80px"></div>`}
  <//>`}function Oo({rows:e}){let t=new Set(qe({config:{rows:e}})),n=e.filter(([o])=>t.has(o.replace(/^config\./,"")));return n.length?s`<table class="kv small">${n.map(([o,,r])=>{let i=Array.isArray(r)?r.map(X).join(", "):`${X(r.min)} \u2026 ${X(r.max)} \xB7 ${r.distinct} values`;return s`<tr><td data-tip=${o}>${o.replace(/^config\./,"")}</td>
      <td data-tip=${i.length>zt?i:void 0}>${i.length>zt?`${i.slice(0,zt-1)}\u2026`:i}</td></tr>`})}</table>`:s`<p class="muted small">No config differs between the runs.</p>`}var Ts=15e3;function Ms({node:e}){let t=q(H),n=de(),[o,r]=hn(),i=e.props.code,l=w(r&&i?{method:"code",params:i,scope:null}:null),[a,c]=y(null),[d,g]=y(120),[m,p]=y({error:null,warnings:[]}),$=x=>{pe&&console.error(`[block ${e.id}] ${x}`),p(u=>({...u,error:x}))},v=L(()=>{});M(()=>{if(!a)return;p(b=>b.own?{...b,own:!1}:b);let x=!0;Ke.n++;let u=()=>{x&&Ke.n--,x=!1};v.current=u;let h=setTimeout(()=>{x&&$(`no first render within ${Ts/1e3} s`),u()},Ts);return()=>{clearTimeout(h),u()}},[a]),M(()=>{let x=a?.contentWindow;if(!x||l.status!=="ready")return;let u=P=>x.postMessage(P,"*"),h=new Map,b=new Sn,j=P=>{if(P.source!==x)return;let C=P.data;switch(C.type){case"hello":u({type:"init",init:{id:e.id,code:l.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:fn.value,pair:nt.value,colormaps:Fe.value,prefs:He(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics,expanded:e.props.expanded?wn():null}});break;case"sub":if(!kn.has(C.call.method)){u({type:"result",id:C.id,result:{status:"error",data:null,error:`${C.call.method} is not available in a custom block`,refreshing:!1}});break}h.get(C.id)?.(),h.set(C.id,nn(C.call,se=>u({type:"result",id:C.id,result:se})));break;case"unsub":h.get(C.id)?.(),h.delete(C.id);break;case"navigate":C.url.startsWith("/")&&N(C.url);break;case"height":b.accept(performance.now())?g(Math.max(40,C.height)):A("its height keeps changing, so it is fixed at its last height");break;case"chrome":p(se=>({...se,own:C.own}));break;case"ready":p(se=>({...se,blank:C.blank,overflow:C.overflow})),v.current();break;case"warn":A(C.message);break;case"hover":Te.set(C.run);break;case"prefs":JSON.stringify(K.value)!==JSON.stringify(C.prefs)&&K.set(C.prefs);break;case"download":case"snapshot":C.href?xn(C.href,C.name)?performance.now()-V>1e3&&(V=performance.now(),Pe().download(C.href,C.name)):A(`a download of ${C.name} was refused: only PNG, SVG and CSV files`):A("it draws no SVG or canvas to download");break;case"figure":Pe().figure(C.spec,C.name).catch(se=>A(`the PDF failed: ${se.message}`));break;case"expand":Cn(C.node)&&Pe().expand(C.node,t);break;case"expand-block":e.props.expanded||Pe().expand(e,t);break;case"close":e.props.expanded&&Re.set(null);break;case"error":$(C.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,T)),v.current();break;default:break}},A=P=>{pe&&console.warn(`[block ${e.id}] ${P}`),p(C=>C.warnings.includes(P)?C:{...C,warnings:[...C.warnings,P]})},V=-1/0,K=He(t.path),Z=Te.subscribe(P=>u({type:"hover",run:P})),O=K.subscribe(P=>u({type:"prefs",prefs:P}));return addEventListener("message",j),u({type:"ping"}),()=>{Z(),O(),removeEventListener("message",j);for(let P of h.values())P()}},[l.status,l.data?.code,a]),M(()=>{let x={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};a?.contentWindow?.postMessage(x,"*")},[t.names,t.colors,t.metrics,a]),M(()=>Fe.subscribe(x=>a?.contentWindow?.postMessage({type:"colormaps",colormaps:x},"*")),[a]),M(()=>{n&&a?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let T=typeof i=="object"?i.path??i.block:String(i??"");gn(e.id,{png:()=>a?.contentWindow?.postMessage({type:"snapshot"},"*")});let f=r&&l.status==="ready"&&!m.error;return s`<div ref=${o} class="custom-block">
    ${m.own?null:s`<div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${f?s`<span class="chart-tools">
            <${W} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>a?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?s`<${W} icon="x" label="Close (Esc)" onClick=${()=>Re.set(null)} />`:s`<${W} icon="maximize" label="Expand" onClick=${()=>Pe().expand(e,t)} />`}
          </span>`:null}
    </div>`}
    <${Q} caption=${e.props.expanded?void 0:e.props.caption} result=${l}>
      ${m.error?s`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${T})</span>
            <pre class="code">${m.error}</pre>
          </div>`:null}
      ${m.warnings.map(x=>s`<${z} kind="warning">${x}<//>`)}
      ${f?s`<div class="custom-frame" data-frame-blank=${m.blank?"1":void 0} data-frame-overflow=${m.overflow?"1":void 0}>
            <iframe key=${l.data.code} ref=${c} sandbox="allow-scripts" ...${zo()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${d}px`} />
          </div>`:null}
    <//>
  </div>`}function zo(){if(!!1)return{src:qt("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1").replace(/@font-face\s*\{[^}]*\}/g,""),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}function Ns({node:e}){let t=Y("main"),n=q(H),o=t.data?.entries??[];return s`<${Q} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!o.length?s`<${z}>No images logged.<//>`:null}
    <div class="images">
      ${o.map(r=>s`<figure key=${`${r.run}/${r.path}`}>
          <img src=${Xt(ye(r.run,n.path),r.path)} alt=${r.caption??e.props.title} loading=${Ue?"eager":"lazy"} />
          <figcaption class="small">step ${Ce(r.step)}${r.caption?` \xB7 ${r.caption}`:""}</figcaption>
        </figure>`)}
    </div>
  <//>`}function Ds({node:e}){let t=Y("main"),n=t.data?.entries??[];return s`<${Q} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?s`<${z}>No text logged.<//>`:null}
    ${n.map(o=>s`<div class="text-entry" key=${`${o.run}/${o.step}`}>
        <div class="muted small">step ${Ce(o.step)}${o.caption?` \xB7 ${o.caption}`:""}</div>
        <pre class="code">${o.text??""}</pre>
      </div>`)}
  <//>`}function Rs({node:e}){let n=`section.${q(H).path}:${e.id}`,[o,r]=y(()=>Ue||ve(n,e.props.open!==!1)),i=()=>{me(n,!o),r(!o)},l=s`${(e.children??[]).map(d=>s`<${ce} key=${d.id} node=${d} />`)}`,a=q(rt);if(!e.props.title)return s`<div class="stack">${l}</div>`;let c=a===e.props.title.toLowerCase();return s`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${o} aria-label=${c?`${o?"Close":"Open"} ${e.props.title}`:void 0}
        data-tip=${c?`${o?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${i}>
      <${k} name=${o?"chevron-down":"chevron-right"} size=${16} />${c?s`<span class="toggle-label code">${a}</span>`:e.props.title}
    </button>
    ${o?s`<div class="stack">${l}</div>`:null}
  </div>`}function Ps({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return s`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>s`<${ce} key=${n.id} node=${n} />`)}
  </div>`}function Ht({node:e,after:t}){let n=q(H),o=oe(n.path),r=e.props.min_width??320,i=e.props.columns,l=i?`grid-template-columns: repeat(${i}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${r}px, 100%), 1fr))`,a=e.children??[],c=a.filter(m=>o.removed.includes(m.id)).map(m=>m.id),d=tn(a.filter(m=>!c.includes(m.id)),o.order[e.id]),g=(m,p)=>{let $=d.map(v=>v.id).filter(v=>v!==m);if($.splice($.indexOf(p),0,m),Qt(n.path,e.id,$),e.id===Yt){let v=f=>a.find(x=>x.id===f)?.data?.main?.params?.y?.[0],T=$.map(f=>n.pins.find(x=>x.y===v(f))).filter(f=>!!f);Zt(n.path,[...T,...n.pins.filter(f=>!T.includes(f))])}};return s`<div class="grid" style=${l}>
    ${d.map(m=>s`<${Bo} key=${m.id} node=${m} path=${n.path} span=${o.spans[m.id]??m.props.span??1}
      columns=${i} onDrop=${p=>p!==m.id&&g(p,m.id)} />`)}
    ${t??null}
    ${c.length?s`<div class="grid-note"><button type="button" class="link small" onClick=${()=>Ae(n.path,c)}>${c.length} hidden · show</button></div>`:null}
  </div>`}var Bt=[1,2,"full"];function Bo(e){let[t,n]=y(!1),o=Bt[(Bt.indexOf(e.span)+1)%Bt.length],r=i=>i==="full"?"full width":`${i} column${i===1?"":"s"}`;return s`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${i=>{i.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${i=>{i.preventDefault(),n(!1),e.onDrop(i.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${i=>i.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${k} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${r(e.span)}; click for ${r(o)}`}
        aria-label=${`Width ${r(e.span)}`} onClick=${()=>en(e.path,e.node.id,o)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${ce} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function At({root:e}){let t=q(H),n=oe(t.path),o=w({method:"keys",params:{from:t.path},scope:t.path}).data,r=e.props.template;if(!r||!1)return null;let i=new Set(n.removed),l=new Set([...t.charted].filter(([$])=>!i.has($)).flatMap(([,$])=>$)),a=n.added.filter($=>!l.has($)).map($=>({block:"line",id:`added-${$}`,props:{y:$},data:{main:{...r,params:{...r.params,y:[$]}}}})),c=new Set([...l,...a.filter($=>!i.has($.id)).map($=>$.props.y)]),d=(o?.metrics?.rows??[]).map($=>$[0]).filter($=>!c.has($));if(!o||!(d.length||a.length))return null;let g=$=>[...t.charted].find(([v,T])=>i.has(v)&&T.includes($))?.[0]??a.find(v=>i.has(v.id)&&v.props.y===$)?.id,m=$=>{let v=g($);v?Ae(t.path,[v]):et(t.path,T=>({added:[...T.added,$]}))},p=d.length?s`<div class="add-chart">
        <span class="add-chart-label"><${k} name="plus" size=${16} /> Add a chart</span>
        <${it} single options=${d} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
          onChange=${([$])=>m($)} />
      </div>`:null;return s`<${I}><${Ht} node=${{block:"grid",id:"added",props:{},children:a}} after=${p} /><//>`}function _s({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[o,r]=y(()=>t.find(a=>a.id===n())?.id??t[0]?.id),i=a=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(a)}`),r(a)},l=t.find(a=>a.id===o)??t[0];return Ue?s`<div class="stack">${t.map(a=>s`<${ce} key=${a.id} node=${a} />`)}</div>`:s`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(a=>s`<button type="button" role="tab" id=${`tab-${a.id}`} aria-selected=${a.id===l?.id}
          aria-controls=${`panel-${a.id}`} onClick=${()=>i(a.id)}>${a.props.title??a.id}</button>`)}
    </div>
    ${l?s`<div class="stack" role="tabpanel" id=${`panel-${l.id}`} aria-labelledby=${`tab-${l.id}`}>
          ${(l.children??[]).map(a=>s`<${ce} key=${a.id} node=${a} />`)}
        </div>`:null}
  </div>`}function Ls({node:e}){let t=Y("main"),n=q(H),o=E(Te),r=e.props,i=En(t.data,r.rows,r.columns,r.lower??{},r.expected??[]),l=B.value.page==="group"?B.value.run:null,a=r.baseline===null||r.baseline===void 0?null:i.find(d=>d.label===String(r.baseline)),c=d=>N(S(n.path,{run:d}),{replace:l!==null});return s`<${Q} title=${r.title} caption=${r.caption} numbered result=${t}>
    ${t.data?s`<div class="table-wrap"><table class="runs scorecard">
          <thead><tr class="small">
            <th data-tip=${r.rows}>${Be(r.rows)}</th>
            ${r.columns.map(d=>s`<th class="num" data-tip=${d}>${Rn(d,n.metrics)}</th>`)}
          </tr></thead>
          <tbody onPointerLeave=${()=>Te.set(null)}>
            ${i.map(d=>{let g=`${d.runs.includes(l??"")?"selected":""}${d.runs.includes(o??"")?" hovered":""}${d.queued?" queued":""}`;return s`<tr key=${d.label} class=${g} data-tip=${d.runs.length?`${d.runs.length} run${d.runs.length>1?"s":""}`:void 0}
                  onClick=${d.runs.length?()=>c(d.runs[0]):void 0}
                  onPointerEnter=${()=>Te.set(d.runs[0]??null)}>
                <td>${d.label}${d===a?s` <${we} tip="the others are compared to this row">baseline<//>`:null}${d.queued?s` <${we}>queued<//>`:null}</td>
                ${d.scores.map((m,p)=>Ho(m,d.live,a?.scores[p]??null))}
              </tr>`})}
          </tbody>
        </table></div>`:s`<div class="skeleton late" style="block-size: 120px"></div>`}
  <//>`}function Ho(e,t,n){if(!e)return s`<td class="num muted">–</td>`;let o=n&&n!==e?`${e.mean-n.mean>=0?"+":"\u2212"}${X(Math.abs(e.mean-n.mean))} against the baseline`:"",r=`${Ct(e.mean)}${e.std===null?"":` \xB1 ${Ct(e.std)}`}, ${e.n} run${e.n>1?"s":""}${o?`. ${o}`:""}`,i=`num score${e.best?" best":""}${t?" live":""}`;return s`<td class=${i} style=${e.shade===null?void 0:`--shade: ${e.shade}`} data-tip=${r}>
    ${X(e.mean)}${e.std===null?null:s`<span class="spread"> ± ${X(e.std)}</span>`}</td>`}var Is={section:Rs,row:Ps,grid:Ht,line:Ln,table:Hn,scorecard:Ls,stat:Bn,images:Ns,text:Ds,proposal:ms,note:ys,output:vs,config:Es,memory:ps,groups:$s,notes:fs,tabs:_s,scatter:In,bar:On,histogram:zn,data_table:Nn,timeline:Dn,custom:Ms,markdown:bs},Ao=new Set(["line","scatter","bar","histogram"]);function ce({node:e}){return Ao.has(e.block)?s`<${Ko} node=${e} />`:s`<${Mt} node=${e} blocks=${Is} />`}function Ko({node:e}){let t=q(H);return oe(t.path).removed.includes(e.id)?s`<div class="grid-note"><button type="button" class="link small" onClick=${()=>Ae(t.path,[e.id])}>1 hidden · show</button></div>`:s`<${Mt} node=${e} blocks=${Is} />`}function Os(e,t){let n=e.split(`
`),o=t.split(`
`),r=n.length,i=o.length,l=Array.from({length:r+1},()=>new Uint32Array(i+1));for(let g=r-1;g>=0;g--)for(let m=i-1;m>=0;m--)l[g][m]=n[g]===o[m]?l[g+1][m+1]+1:Math.max(l[g+1][m],l[g][m+1]);let a=[],c=0,d=0;for(;c<r&&d<i;)n[c]===o[d]?(a.push({kind:"same",text:n[c]}),c++,d++):l[c+1][d]>=l[c][d+1]?a.push({kind:"removed",text:n[c++]}):a.push({kind:"added",text:o[d++]});for(;c<r;)a.push({kind:"removed",text:n[c++]});for(;d<i;)a.push({kind:"added",text:o[d++]});return a}function zs(e,t=3){let n=[],o=0;for(;o<e.length;){if(e[o].kind!=="same"){n.push(e[o++]);continue}let r=o;for(;r<e.length&&e[r].kind==="same";)r++;let i=o===0?0:t,l=r===e.length?0:t;r-o>i+l+1?n.push(...e.slice(o,o+i),{kind:"skip",count:r-o-i-l},...e.slice(r-l,r)):n.push(...e.slice(o,r)),o=r}return n}var Kt={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",config:"config",timeline:"timeline",proposal:"predictions"};function Bs(e){if(Kt[e.block])return Kt[e.block];if(e.block==="row"||e.block==="grid"){let n=new Set((e.children??[]).map(r=>Kt[r.block])),[o]=n;if(n.size===1&&o)return o}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function kt(e){let t=w(Xe(e.path)),n=de(),o=D(t.data),r=ze(()=>ot(o.map(p=>p["run.id"]),n),[t.data,n]),i=ze(()=>new Map(o.map(p=>[p["run.id"],p["run.name"]??p["run.id"]])),[t.data]),l=oe(e.path),a=e.plain?"view plain":"sections view";if(!e.view)return s`<div class=${a}>${e.before}
      ${e.plain?s`<div class="skeleton late" style="block-size: 320px"></div>`:s`<${I} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let c=e.view.view,d={path:e.path,colors:r,names:i,metrics:e.view.metrics??{},charted:Ut(c),pins:l.main??e.view.pins??[]};if(e.plain)return s`<div class=${a}><${H.Provider} value=${d}><${ce} node=${c} /><//></div>`;let g=c.block==="section"&&!c.props.title?c.children??[]:[c],m=g.map(p=>Ut(p).size>0).lastIndexOf(!0);return s`<div class=${a}>${e.before}
    <${H.Provider} value=${d}>
      ${g.map((p,$)=>{let v=Bs(p);return s`<${jt} key=${p.id}><${I} label=${v}><${rt.Provider} value=${v}><${ce} node=${p} /><//><//>
          ${$===m?s`<${At} root=${c} />`:null}<//>`})}
      ${m===-1?s`<${At} root=${c} />`:null}
    <//>
  </div>`}function Ut(e,t=new Map){e.block==="line"&&t.set(e.id,e.data?.main?.params?.y??[]);for(let n of e.children??[])Ut(n,t);return t}function Hs(e){if(null)return s`<div class="view-source small"><${k} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=E(B),o=n.page==="group"&&n.version,r=t.versions?s`<a href=${S(e.path,{history:!0})}><${k} name="history" size=${14} /> history (${t.versions})</a>`:null,i;switch(t.source){case"draft":i=s`draft <b>${t.draft}</b>`;break;case"view":i=s`${t.title?s`<em>${t.title}</em> · `:null}saved ${U(be(t.version))} by ${t.author??"unknown"}`;break;default:i=s`the built-in view`}return s`<div class="view-source small">
    <${k} name="layout" size=${14} /><span>${i}</span>
    ${o?s`<a href=${S(e.path)}>an older version · show the current one</a>`:null}
    ${r}
    ${t.outdated?.length&&!o?s`<${Uo} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||o?null:s`<${Fo} path=${e.path} />
        <${Wo} path=${e.path} view=${t} />`}
  </div>`}function Uo(e){let[t,n]=y(null),o=e.outdated.map(i=>i.name).join(", ");return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{await Gn(e.path)}catch(i){n(i.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${o} exists; update re-pins this view to it (a new version)`}>
      <${k} name="update" size=${14} /> update ${o}</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function Fo(e){let[t,n]=y(null);return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{_e.set(await dt(e.path,null,""))}catch(r){n(r.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${k} name="file-text" size=${14} /> add text</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function Wo(e){let t=oe(e.path),n=Jt(t),[o,r]=y(!1),[i,l]=y(e.view.title??""),[a,c]=y(e.view.finding??""),[d,g]=y(null),[m,p]=y(!1);if(!n&&!o)return null;let $=async v=>{v.preventDefault(),p(!0),g(null);try{let T={charts:t.charts,view:t.view,added:t.added,removed:t.removed,order:t.order,spans:t.spans,main:t.main};await F("save_view",{path:e.path,prefs:T,title:i,finding:a}),et(e.path,()=>({view:{},charts:{},added:[],removed:[],order:{},spans:{},main:null})),De(f=>["view","view_history","summary"].includes(f.method)&&f.scope===e.path),r(!1)}catch(T){g(T.message)}finally{p(!1)}};return o?s`<form class="save-form" onSubmit=${$}>
    <${je} label="Title"><input value=${i} onInput=${v=>l(v.target.value)} /><//>
    <${je} label="Finding"><input value=${a} placeholder="the key result in one sentence"
        onInput=${v=>c(v.target.value)} /><//>
    <div class="save-actions">
      <${ee} type="submit" icon=${m?"hourglass":"save"} disabled=${m}>${m?"Saving\u2026":"Save as view"}<//>
      <${ee} icon="x" kind="quiet" onClick=${()=>r(!1)}>Cancel<//>
      ${d?s`<span class="bad-text small">${d}</span>`:null}
    </div>
  </form>`:s`<${ee} icon="save" class="save-view" onClick=${()=>r(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function As(e){let t=w(ns(e.path)),n=t.data?.entries??[],[o,r]=y(null),i=o??n.slice(0,2).map(a=>a.version).reverse(),l=a=>{let c=i.includes(a)?i.filter(d=>d!==a):[...i,a].slice(-2);r(c.sort())};return t.status==="error"?s`<${z} kind="error">${t.error}<//>`:s`<section class="history">
    ${t.data&&!n.length?s`<${z}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((a,c)=>s`<li key=${a.version} class=${i.includes(a.version)?"picked":""}>
          <label><input type="checkbox" checked=${i.includes(a.version)} onChange=${()=>l(a.version)} />
            <span class="num muted" data-tip=${a.version}>${U(a.time)}</span>
            <b>${a.title??"untitled"}</b><span class="muted">${a.author??""}</span>
            ${a.message?s`<span>${a.message}</span>`:null}</label>
          <a href=${c===0?S(e.path):S(e.path,{version:a.version})}
            onClick=${d=>{d.preventDefault(),N(c===0?S(e.path):S(e.path,{version:a.version}))}}>${c===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${i.length===2?s`<${jo} path=${e.path} a=${i[0]} b=${i[1]} />`:null}
  </section>`}function jo(e){let t=a=>({method:"view_show",params:{group:e.path,version:a},scope:e.path}),n=w(t(e.a)).data,o=w(t(e.b)).data,r=w(fe(e.path,e.a)).data,i=w(fe(e.path,e.b)).data,l=n&&o?zs(Os(n.yaml,o.yaml)):[];return s`<div class="compare">
    <h3 class="block-title heading">Changes from ${U(be(e.a))} to ${U(be(e.b))}</h3>
    <pre class="diff code">${l.map(a=>a.kind==="skip"?s`<div class="diff-skip">⋯ ${a.count} unchanged lines</div>`:s`<div class=${`diff-${a.kind}`}>${a.kind==="added"?"+ ":a.kind==="removed"?"\u2212 ":"  "}${a.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${r?.title??e.a}</h3><${kt} path=${e.path} view=${r} plain /></div>
      <div><h3 class="block-title heading">${i?.title??e.b}</h3><${kt} path=${e.path} view=${i} plain /></div>
    </div>
  </div>`}function Ks(e){return ss(e.path),e.history?s`<div class="page"><div class="sections">
      <${I} label=${Us(e.path)}><${Ot} path=${e.path} /><//>
      <${I} label="history"><${As} path=${e.path} /><//>
    </div></div>`:s`<div class="page">
    <${Go} path=${e.path} version=${e.version??null} draft=${e.draft??null} hiddenRuns=${e.hiddenRuns??!1} />
  </div>`}function Go(e){let t=oe(e.path).main,n=wt(fe(e.path,e.version,e.draft,t),`${e.path}|${e.version}|${e.draft}`);M(()=>{n.status==="ready"&&requestAnimationFrame(cn)},[n.status==="ready"]),M(()=>{let r=i=>ks(i.target.closest?.(".chart-frame")??null);return addEventListener("click",r,!0),()=>removeEventListener("click",r,!0)},[]);let o=s`
    <${I} label=${Us(e.path)}>
      <${Ot} path=${e.path} finding=${n.data?.finding} />
      ${n.data?s`<${Hs} path=${e.path} view=${n.data} />`:null}
    <//>
    ${ie(e.path.split("/").pop()??"")?null:s`${e.hiddenRuns?s`<${xs} path=${e.path} />`:null}<${Cs} path=${e.path} />`}`;return n.status==="error"?s`<div class="sections">${o}
      <${I} label="view">
        ${Vo(e.path,n.error)?s`<${z} kind="warning">${n.error} The page fills in once the remote answers again.<//>`:s`<${z} kind="error">${n.error}<//>`}
      <//>
    </div>`:s`<${kt} path=${e.path} view=${n.data} before=${o} />`}function Us(e){return ie(e.split("/").pop()??"")?"run":"group"}function Vo(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function Fs(e){M(()=>{Ne(fe(e.id)).then(n=>N(S(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=w(fe(e.id));return t.status==="error"?s`<div class="page"><${z} kind="error">${t.error}<//></div>`:s`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var qo={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},Ft=20,Oe=-1,Xo=[["day",86400],["week",7*86400],["month",30*86400]];function js(e){let t=D(w(ue()).data).map(a=>a.path),n=w({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),o=w({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});Je("Timeline",D(n.data).filter(a=>a["run.status"]==="running").length);let r=Date.now()/1e3,i=D(n.data).filter(a=>a["run.created_at"]).map((a,c)=>({id:a["run.id"],name:a["run.name"]??a["run.id"],group:a["run.group"],status:a["run.status"],start:Date.parse(a["run.created_at"])/1e3,end:a["run.ended_at"]?Date.parse(a["run.ended_at"])/1e3:r,lane:c})),l=(o.data?.entries??[]).map(a=>({id:a.id,type:a.type,group:a.group,description:a.description,t:Date.parse(be(a.id))/1e3}));return s`<div class="page timeline-page"><div class="sections">
    <${I} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${je} label="Group" inline>
          <select value=${e.from} onChange=${a=>N(tt(a.target.value),{replace:!0})}>
            ${t.map(a=>s`<option value=${a}>${a==="."?"everything":a}</option>`)}
          </select><//>
        <span class="muted small">${i.length} runs · ${l.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${I} label="runs">
      ${n.status==="error"?s`<${z} kind="error">${n.error}<//>`:null}
      ${n.data&&o.data?s`<${Yo} bars=${i} marks=${l} />`:s`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function Yo(e){let t=de(),n=L(null),o=[...e.bars.flatMap(f=>[f.start,f.end]),...e.marks.map(f=>f.t)],r=o.length?Ws(Math.min(...o),Math.max(...o)):Ws(Date.now()/1e3-86400,Date.now()/1e3),[i,l]=y(r),a=e.bars.length,c=Math.min(900,Math.max(160,(a+1.5)*Ft+40)),g=Pn(n,_n,t?(f=>{let x=Tn(i[0],i[1]),u=b=>f.colors[qo[b]??"muted"],h=b=>f.colors[b==="verdict"?"good":b==="decision"?"accent":b==="question"?"warn":"muted"];return{style:$n(f),height:c,x:{range:i,log:!1,format:b=>Mn(b,x.step),label:"",splits:x.at},y:{range:[Oe-.8,a+.5],log:!1,reverse:!0,label:"",size:150,splits:a<=40?[Oe,...e.bars.map(b=>b.lane)]:[Oe],format:b=>b===Oe?"notes":tr(e.bars[Math.round(b)]?.name??"")},draw:({ctx:b,x:j,y:A,px:V,focused:K})=>{let Z=Ft*.62*V;for(let O of e.bars){let P=j(O.start),C=Math.max(3*V,j(O.end)-P);b.fillStyle=K!==null&&K!==O.id?pn(u(O.status),.35):u(O.status),b.beginPath(),b.roundRect(P,A(O.lane)-Z/2,C,Z,3*V),b.fill()}for(let O of e.marks){let P=j(O.t),C=A(Oe),se=(K===O.id?6:4.5)*V;b.fillStyle=h(O.type),b.beginPath(),b.moveTo(P,C-se),b.lineTo(P+se,C),b.lineTo(P,C+se),b.lineTo(P-se,C),b.closePath(),b.fill()}},hit:(b,j,A,V)=>{if(Math.abs(j-V(Oe))<Ft/2){let O=er(e.marks,P=>Math.abs(A(P.t)-b),8);return O?{key:O.id,rows:Zo(O)}:null}let K=Math.round((j-V(0))/(V(1)-V(0))),Z=e.bars.find(O=>O.lane===K&&A(O.start)-3<=b&&b<=Math.max(A(O.end),A(O.start)+3)+3);return Z?{key:Z.id,rows:Jo(Z)}:null},onClick:b=>{let j=e.marks.find(A=>A.id===b);j?N(S(j.group,{drawer:!0})):N(re(b))}}})(t):null,[i,e.bars,e.marks],t),m=f=>{if(!g.current)return;f.preventDefault();let x=g.current.xAt(f.clientX),u=Math.exp(f.deltaY*.0015);l(([h,b])=>Wt([x-(x-h)*u,x+(b-x)*u],r))},p=L(null),$=f=>p.current={x:f.clientX,range:i},v=f=>{if(!p.current||!g.current||!(f.buttons&1))return;let x=(f.clientX-p.current.x)*g.current.xPerPixel(),[u,h]=p.current.range;Math.abs(f.clientX-p.current.x)>3&&l(Wt([u-x,h-x],r))},T=Math.max(...o,Date.now()/1e3);return s`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${Xo.map(([f,x])=>s`<button type="button" role="radio" aria-checked=${Math.abs(i[1]-i[0]-x)<1}
          onClick=${()=>l(Wt([T-x,T+x*.02],[Math.min(r[0],T-x),r[1]]))}>last ${f}</button>`)}
      <button type="button" role="radio" aria-checked=${i[0]===r[0]&&i[1]===r[1]} onClick=${()=>l(r)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${c}px`}
      onWheel=${m} onPointerDown=${$} onPointerMove=${v} onPointerUp=${()=>p.current=null}></div>
    <p class="muted small">${Qo(t)}</p>
  </div>`}function Jo(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:U(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:Se(e.end-e.start),color:null}]}function Zo(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:U(new Date(e.t*1e3).toISOString()),color:null}]}function Qo(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function er(e,t,n){let o=null,r=n;for(let i of e){let l=t(i);l<r&&([o,r]=[i,l])}return o}function Ws(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function Wt([e,t],n){let o=Math.min(n[1]-n[0],Math.max(60,t-e)),r=Math.max(n[0],Math.min(e,n[1]-o));return[r,r+o]}function tr(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function Gs(){let e=E(Re),t=L(null);if(M(()=>{let r=t.current;if(!r||!e)return;r.showModal();let i=()=>Re.set(null);return r.addEventListener("close",i),()=>r.removeEventListener("close",i)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},o=String(n.props.title??n.props.y??"Chart");return s`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${o} closedby="any">
    <${H.Provider} value=${e.view}><${ce} node=${n} /><//>
  </dialog>`}function Vs(e,t){let n=e.toLowerCase(),o=t.toLowerCase();if(!n)return 1;let r=o.indexOf(n);if(r>=0)return 100-Math.min(r,50)-o.length/100;let i=0,l=0;for(let a of o)if(a===n[i]?i++:i>0&&l++,i===n.length)return 40-Math.min(l,39);return 0}function Xs(e){let[t,n]=y(e.query),[o,r]=y(0),i=L(null),l=D(w(ue()).data),a=D(w(mt()).data);M(()=>{let u=i.current;u.showModal();let h=()=>ne.set(null);u.addEventListener("close",h);let b=!1,j=K=>{let Z=u.getBoundingClientRect();return K.clientX<Z.left||K.clientX>Z.right||K.clientY<Z.top||K.clientY>Z.bottom},A=K=>b=j(K),V=K=>b&&j(K)&&u.close();return"closedBy"in HTMLDialogElement.prototype||(u.addEventListener("pointerdown",A),u.addEventListener("pointerup",V)),()=>{u.removeEventListener("close",h),u.removeEventListener("pointerdown",A),u.removeEventListener("pointerup",V)}},[]);let c=()=>i.current?.close(),d=u=>()=>N(u),g=B.value,m=g.page==="group"?g.path:".",p=(u,h,b,j)=>({section:"Commands",label:u,detail:h,sym:{icon:b,tone:"muted",label:u},run:j}),v=[...l.map(u=>({section:"Groups",label:u.path==="."?"local":u.path,detail:`${u.runs} runs${u.proposal?` \xB7 ${u.proposal}`:""}`,sym:R("research",u.status),run:d(S(u.path))})),...a.map(u=>({section:"Runs",label:u["run.name"]??u["run.id"],detail:`${u["run.status"]} \xB7 ${u["run.path"]}`,sym:R("run",u["run.status"]),run:d(S(u["run.path"]))})),p("Theme: light","","sun",()=>st("light")),p("Theme: dark","","moon",()=>st("dark")),p("Theme: follow the system","","monitor",()=>st("system")),p("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),p("Show notes and timeline","i","file-text",d(S(m,{drawer:!0}))),p("Show or hide the sidebar","\u2318B","panel-left",()=>te.set(!te.value)),p(ae.value?"Resume live updates":"Pause live updates","p",ae.value?"play":"pause",()=>ae.set(!ae.value)),p("Keyboard shortcuts","?","keyboard",()=>he.set(!0)),p("Settings","","settings",d("/settings/appearance"))].map(u=>({it:u,s:Math.max(Vs(t,u.label),Vs(t,u.detail)*.5)})).filter(u=>u.s>0).sort((u,h)=>h.s-u.s||qs(u.it.section)-qs(h.it.section)).slice(0,60).map(u=>u.it),T=u=>{u&&(c(),u.run())},f=u=>{if(u.key==="ArrowDown")r(Math.min(v.length-1,o+1));else if(u.key==="ArrowUp")r(Math.max(0,o-1));else if(u.key==="Enter")T(v[o]);else return;u.preventDefault()},x="";return s`<dialog class="sheet" ref=${i} aria-label="Search" closedby="any">
    <div class="palette-input"><${k} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${v[o]?`pal-${o}`:void 0}
        onInput=${u=>{n(u.target.value),r(0)}} onKeyDown=${f} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${v.map((u,h)=>{let b=u.section!==x&&!t?x=u.section:null;return s`${b?s`<li class="palette-head small" role="presentation">${b}</li>`:null}
          <li id=${`pal-${h}`} class="item" role="option" aria-selected=${h===o}
              onMouseMove=${()=>r(h)} onClick=${()=>T(u)}>
            <${_} spec=${u.sym} /><span class="label">${u.label}</span><span class="detail small">${u.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function qs(e){return["Groups","Runs","Commands"].indexOf(e)}function xt(e,t=[]){let n=new Map,o=(a,c={})=>({path:a,name:a==="."?"local":a.split("/").pop(),runs:c.runs??0,running:c.running??0,failed:(c.failed??0)+(c.killed??0)+(c.lost??0),status:c.status??null,children:[]});for(let a of e)n.set(a.path,o(a.path,a));(t.length===0||t.some(a=>a.name==="."))&&!n.has(".")&&n.set(".",o("."));for(let a of t){let c=a.name;n.has(c)||n.set(c,o(c)),Object.assign(n.get(c),{state:a.state,error:a.error})}for(let a of n.values()){if(G(a.path))continue;let c=a.path.lastIndexOf("/"),d=c<0?".":a.path.slice(0,c);(n.get(d)??n.get(Ee(a.path))??n.get(".")).children.push(a)}for(let a of n.values())a.children.sort((c,d)=>c.name.localeCompare(d.name));let i=[...n.values()].filter(a=>a.path!=="."&&G(a.path)).sort((a,c)=>a.name.localeCompare(c.name)),l=n.get(".");return l?[l,...i]:i}function Ys(e,t,n,o=new Set){let r=[],i=n.toLowerCase(),l=a=>{(!i||a.path.toLowerCase().includes(i)||Js(a,i))&&(r.push(a),(i||(G(a.path)?!o.has(a.path):t.has(a.path)))&&a.children.forEach(l))};return e.forEach(l),r}function Js(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||Js(n,t))}function Zs(e,t){if(!t||G(t))return e;let n=t.split("/"),o=new Set(e);for(let r=t.startsWith("@")?2:1;r<n.length;r++)o.add(n.slice(0,r).join("/"));return o.size===e.size?e:o}function Qs(e,t){if(G(t))return e;let n=t.lastIndexOf("/"),o=n<0?".":t.slice(0,n),r=i=>i.path===o?i:i.children.map(r).find(l=>l)??null;return e.map(r).find(i=>i)?.children??[]}function eo(e){return G(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function to(){let e=E(B),t=w(ue()),[n,o]=y(()=>new Set(ve("open",[]))),[r,i]=y(()=>new Set(ve("closed-hosts",[]))),[l,a]=y(""),c=L(null),d=e.page==="group"?e.path:null,g=xt(D(t.data),t.data?.meta?.sources??[]),m=Ys(g,n,l,r),p=f=>G(f)?!r.has(f):n.has(f),$=(f,x)=>{let u=x??!p(f);if(G(f)){let b=new Set(r);u?b.delete(f):b.add(f),me("closed-hosts",[...b]),i(b);return}let h=new Set(n);u?h.add(f):h.delete(f),me("open",[...h]),o(h)},v=L(d);return M(()=>{let f=Zs(n,d);f!==n&&(me("open",[...f]),o(f)),d!==v.current&&d&&!G(d)&&r.has(Ee(d))&&$(Ee(d),!0),v.current=d},[d]),s`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${k} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${l} aria-label="Filter groups"
        onInput=${f=>a(f.target.value)} />
    </label>
    <div class="tree" ref=${c} onKeyDown=${f=>{let x=[...c.current?.querySelectorAll("a.tree-item")??[]],u=x.indexOf(document.activeElement),h=m[u];switch(f.key){case"ArrowDown":x[Math.min(x.length-1,u+1)]?.focus();break;case"ArrowUp":x[Math.max(0,u-1)]?.focus();break;case"ArrowRight":h?.children.length&&$(h.path,!0);break;case"ArrowLeft":h?.children.length&&p(h.path)?$(h.path,!1):h&&x[m.findIndex(b=>b.path===sr(h.path))]?.focus();break;default:return}f.preventDefault()}} role="tree">
      ${m.map(f=>s`<${nr} key=${f.path} node=${f} current=${f.path===d}
        open=${p(f.path)||!!l} filtering=${!!l} onToggle=${()=>$(f.path)} />`)}
    </div>
  </nav>`}function nr(e){let t=e.node,n=()=>Ye(t.path),o=t.children.length>0,r=t.state==="unreachable";return s`<a class=${`tree-item${e.current?" current":""}${G(t.path)?" source-root":""}`} href=${S(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${o?e.open:void 0}
      style=${`padding-inline-start:${8+eo(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${i=>{i.metaKey||i.ctrlKey||(i.preventDefault(),e.current&&o&&!e.filtering?e.onToggle():N(S(t.path)))}}>
    <span class=${`twisty${o?" expandable":""}`} aria-disabled=${o&&e.filtering?"true":void 0}
      onClick=${i=>{o&&(i.preventDefault(),i.stopPropagation(),e.filtering||e.onToggle())}}>
      ${o?s`<${k} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    ${G(t.path)?s`<${_} size=${14} spec=${{icon:r?"cloud-off":"server",tone:"muted",label:r?`Unreachable: ${t.error??"no answer"}`:t.path==="."?"This machine":`Remote host ${t.name}`}} />`:null}
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?s`<${_} spec=${R("run","running")} size=${14} />`:null}
      ${t.failed?s`<${_} spec=${{...R("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function sr(e){if(G(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function so(){let e=E(B),t=E(te),n=E(ne),o=E(he),r=L(null);M(()=>ln(()=>r.current),[]),M(()=>(addEventListener("keydown",no),()=>removeEventListener("keydown",no)),[]);let i=e.page==="group"&&e.drawer,l;switch(e.page){case"group":l=s`<${Ks} key=${`${e.path} ${e.version} ${e.draft} ${e.history} ${e.hiddenRuns}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} hiddenRuns=${e.hiddenRuns} />`;break;case"run":l=s`<${Fs} id=${e.id} />`;break;case"settings":l=s`<${is} />`;break;case"timeline":l=s`<${js} key=${e.from} from=${e.from} />`;break;default:l=s`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return pe||!1?s`<main class="main render-main" ref=${r}>${l}</main>`:s`<div class=${`shell${t?"":" no-sidebar"}${i?" with-drawer":""}`}>
    <${cs} />
    ${t?s`<${to} />`:null}
    <main class="main" ref=${r}>${l}</main>
    ${i?s`<${ws} path=${e.path} run=${e.run} />`:null}
    <${ds} />
    ${n!==null?s`<${Xs} query=${n} />`:null}
    ${o?s`<${rr} />`:null}
    <${Gs} />
  </div>`}function no(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),ne.set(ne.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),te.set(!te.value);return}if(e.key==="Escape"){if(ne.value!==null||he.value)return;let o=B.value;return o.page==="group"&&o.run?N(S(o.path,{drawer:!0}),{replace:!0}):o.page==="group"&&o.drawer?N(S(o.path),{replace:!0}):void 0}if(t||e.altKey||rs(e)||ne.value!==null||he.value)return;let n=B.value;switch(e.key){case"/":e.preventDefault(),ne.set("");break;case"?":he.set(!he.value);break;case"p":ae.set(!ae.value);break;case"i":n.page==="group"&&N(S(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":te.set(!te.value);break;case"[":case"]":n.page==="group"&&or(n.path,e.key==="]"?1:-1);break}}async function or(e,t){let n=await Ne(ue()),o=Qs(xt(D(n),n?.meta?.sources??[]),e),r=o.findIndex(l=>l.path===e),i=o[r+t];i&&N(S(i.path))}function rr(){let e=L(null);return M(()=>{let t=e.current;t.showModal();let n=()=>he.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),s`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${ft.map(([t,n])=>s`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${ee} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}dn();if(pe){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&($e.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Ke.n,un&&vn()}An();var ar=F("meta").then(e=>(pe&&(e={...e,settings:{...e.settings,theme_mode:$e.value}}),ht(e),e));!pe&&!!1&&an(async()=>{let[e,t]=await Promise.all([ar,F("meta")]);e.bundle!==t.bundle?location.reload():ht(t)});Gt(s`<${so} />`,document.getElementById("app"));
