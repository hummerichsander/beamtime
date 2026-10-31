import{$ as ne,$a as rn,A as St,Aa as rt,B as Tt,Ba as Ht,C as ge,Ca as ot,D as ve,Da as je,E as k,Ea as Fe,F as ze,Fa as At,G as re,Ga as Ut,H as Ne,Ha as Kt,I as Be,Ia as jt,J as q,Ja as Ft,K as W,L as Ct,Ma as Wt,N as R,Na as Gt,O as Mt,Oa as Vt,P as Dt,Pa as Xt,Q as oe,Qa as qt,R as _e,Ra as Yt,S as Nt,Sa as Jt,T as He,Ta as Zt,U as tt,V as ie,Va as Qt,W as Lt,Wa as en,X as nt,Xa as tn,Y as Ae,Ya as nn,Z as Y,Za as sn,_ as te,_a as an,aa as Ue,ab as on,ba as Pt,c as bt,ca as Re,d as s,da as Le,e as h,f as M,fa as Ot,g as yt,ga as It,h as B,ha as v,i as Te,ia as T,j as me,ja as ee,ka as z,la as P,m as $e,ma as st,n as _,na as G,o as Ce,oa as be,p as Me,pa as fe,qa as ye,ra as A,s as H,t as De,u as he,ua as K,v as et,va as zt,w,wa as at,x as xt,xa as Bt,y as Q,ya as Ke,z as Et,za as D}from"./chunks/chunk-GPCHZ4OI.js";import{a as wt,b as kt}from"./chunks/chunk-O2K4N3UR.js";import{e as _t,f as Rt}from"./chunks/chunk-MPNRY2JX.js";import"./chunks/chunk-VC46IEJQ.js";function we(e,t){ge(n=>t.includes(n.method)&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var it=["notes","timeline","groups","check","card","memory_show","status"];async function lt(e,t){let n=e.meta??{};await H("note_add",{group:e.group,type:e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),we(e.group,it)}async function ln(e,t,n,a){await H("note_add",{group:e,type:t,description:n,body:a}),we(e,it)}async function cn(e,t){await H("memory_update",{group:e,body:t}),we(e,["memory_show","status"])}async function un(e,t){let n=await H("proposal_show",{group:e}),a=Object.fromEntries(Object.entries(n.proposal??{}).filter(([r])=>!["schema","author","user","supersedes"].includes(r)));await H("proposal_set",{group:e,proposal:{...a,statement:t}}),we(e,["groups","proposal_show","check","summary"])}async function dn(e){await H("note_rm",{note:e.id}),we(e.group,it)}async function mn(e,t,n){await H("name",{run:e,name:n}),we(t,["card","runs","groups","summary","series"])}async function We(e,t,n){let a=await H("view_text",{path:e,id:t,text:n});return ge(r=>["view","view_history"].includes(r.method)&&r.scope===e),a.id}async function pn(e){await H("view_upgrade",{group:e}),ge(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var ke=new $e(null);async function $n(e,t){return await H("set",{key:e,value:t}),H("meta")}var V=new $e(Ce("sidebar",!0)),X=new $e(null),le=new $e(!1),xe=new $e(null);V.subscribe(e=>Me("sidebar",e));var fn=Ce("visit",Date.now());Me("visit",Date.now());function hn(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var Ge=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var ps=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function Ve(e){xe.set(e),He.set(e.theme),e.settings?.theme_mode&&ie.set(e.settings.theme_mode),nt()}async function ct(e,t){e==="theme_mode"&&(ie.set(t),nt()),Ve(await $n(e,t))}function gn(){let e=_(ie),t=ne(),n=_(xe),[a,r]=h(null);M(()=>{document.title="Settings \xB7 Beamtime"},[]);let o=(i,d)=>{r(null),ct(i,d).catch(u=>r(u.message))},l=n?.settings??{};return s`<div class="page settings">
    <header class="header"><h1 class="title" tabindex="-1">Settings</h1></header>
    <p class="muted small">Changes are written to <code>${l.file??"beamtime.yaml"}</code>, the project's settings.</p>
    ${a?s`<${z} kind="error">${a}<//>`:null}
    <h2>Appearance</h2>
    <div class="settings-rows">
      <span class="field-label">Mode</span>
      <div class="segmented" role="radiogroup" aria-label="Theme mode">
        ${ps.map(([i,d,u])=>s`<button type="button" role="radio" aria-checked=${e===i} onClick=${()=>o("theme_mode",i)}>
          <${v} name=${d} size=${15} />${u}</button>`)}
      </div>
      <span class="field-label">Theme</span>
      <select value=${l.theme} onChange=${i=>o("theme",i.target.value)}>
        ${(n?.themes??[]).map(i=>s`<option value=${i}>${i}</option>`)}
      </select>
    </div>
    <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files go in <code>themes/</code> next to beamtime.yaml.</p>
    ${(n?.theme?.problems??[]).map(i=>s`<${z} kind="warning">${i}<//>`)}
    <h2>Figures</h2>
    <div class="settings-rows">
      <span class="field-label">Style sheets</span>
      ${(n?.figure_styles??[]).length?s`<${Ke} options=${n.figure_styles} value=${l.figure_style??[]} label="Style sheets"
            placeholder="Add a style" onChange=${i=>o("figure_style",i)} />`:s`<span class="muted small"><code>${JSON.stringify(l.figure_style??[])}</code>; choosing others needs the figures
            extra: <code>uv add matplotlib scienceplots</code></span>`}
    </div>
    <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(l.figure_style??[])})</code>, in this order
      (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
      <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <h2>Keyboard</h2>
    <table class="kv">${Ge.map(([i,d])=>s`<tr><td><kbd>${i}</kbd></td><td>${d}</td></tr>`)}</table>
    <h2>About</h2>
    <table class="kv">
      <tr><td class="muted">version</td><td>${n?.version}</td></tr>
      <tr><td class="muted">root</td><td><code>${n?.root}</code></td></tr>
      <tr><td class="muted">log dir</td><td><code>${n?.logdir}</code></td></tr>
    </table>
  </div>`}var se=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),ce=(e,t=null,n=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{}},scope:e}),ut=e=>({method:"summary",params:{path:e},scope:e}),dt=e=>({method:"groups",params:{from:e,depth:0},scope:e}),vn=e=>({method:"check",params:{group:e},scope:e}),bn=e=>({method:"proposal_show",params:{group:e},scope:e}),Xe=(e,t)=>({method:"card",params:{run:Ne(e,t)},scope:t}),yn=(e,t)=>({method:"output",params:{run:Ne(e,t),tail:30},scope:t}),Pe=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),wn=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),kn=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),xn=()=>({method:"status",params:{},scope:"."}),qe=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function Oe(e){for(let t of[ce(e),dt(e),Pe(e),ut(e)])et(t);he(ce(e)).then(t=>{for(let n of En(t.view))et(n)}).catch(()=>{})}function En(e){return e?[...$s.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(En)]:[]}var $s=new Set(["line","custom"]),Sn=e=>({method:"view_history",params:{group:e},scope:e});var Tn={system:"light",light:"dark",dark:"system"},fs={system:"monitor",light:"sun",dark:"moon"};function Cn(){let e=_(xe),t=_(ie),n=_(V);return s`<header class="topbar">
    <${K} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>V.set(!n)} />
    <a class="project" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search" onClick=${()=>X.set("")} aria-label="Search (⌘K)">
      <${v} name="search" size=${15} /><span class="search-label">Search groups, runs, commands</span><kbd>⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${hs} />
      <${K} icon=${fs[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${Tn[t]})`}
        onClick=${()=>{ct("theme_mode",Tn[t])}} />
      <a class="icon-button" href=${ze(W.value.page==="group"?W.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${v} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${v} name="settings" size=${16} /></a>
    </div>
  </header>`}function hs(){let t=(w(se()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?s`${[{name:"local",state:"connected"},...t].map(n=>s`<a class=${`source ${n.state}`}
      href=${k(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${v} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:s`<span class="source" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${v} name="server" size=${15} /> local</span>`}function gs(e){let[t,n]=h(Date.now());return M(()=>{let a=setInterval(()=>n(Date.now()),e);return()=>clearInterval(a)},[e]),t}function vs(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function Mn(){let e=_(Et),t=_(Q),n=_(St),a=_(W),r=gs(5e3),o=w(xn()).data,l=P(w(qe()).data),i=_(xe),d=o?.daemon,u=o?.runs?.running??0,c=l.filter(C=>C["run.status"]==="failed"&&vs(C["run.ended_at"])>fn).length,$=o?.meta?.freshness,[p,f,E]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&d?["",`live \xB7 updated ${A(new Date(n).toISOString(),r)}`,`beamtime serve, pid ${d.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return s`<footer class="statusbar">
    <span class="status-item" data-tip=${E}><span class=${`live-dot ${p}`}></span>${f}</span>
    ${u?s`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>X.set("running")}>
          <${v} name="circle-dot" size=${14} class="tone-running" />${u} running</button>`:null}
    ${c?s`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>X.set("failed")}>
          <${v} name="circle-x" size=${14} />${c} failed since your last visit</button>`:null}
    ${$?.behind?s`<span class="status-item warn-text" data-tip=${$.text}><${v} name="hourglass" size=${14} />${$.behind} runs behind</span>`:null}
    ${$?.damaged?.length?s`<span class="status-item warn-text" data-tip=${$.damaged.join(`
`)}><${v} name="triangle-alert" size=${14} />${$.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${a.page==="group"&&a.run?s`<span class="status-item"><${v} name="activity" size=${14} />1 run selected</span>`:null}
    <${K} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>Q.set(!t)} />
    ${i?.outdated?s`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item subtle">${i?.version?`beamtime ${i.version}`:""}</span>
  </footer>`}var Dn=null;function Ye(e){let t=B(null),[n,a]=h(null),[r,o]=h(!1),[l,i]=h(!1);M(()=>{let $=!0;return Dn??=import("./chunks/md-SW3VT2BQ.js"),Dn.then(p=>p.render(e.text??"")).then(p=>$&&a(p)),()=>{$=!1}},[e.text]),yt(()=>{let $=t.current;if(!$||!e.clamp)return;let p=()=>i($.scrollHeight>$.clientHeight+2),f=new ResizeObserver(p);return f.observe($),()=>f.disconnect()},[e.clamp,n]);let d=e.clamp&&!r,u=`md${d?" clamped":""}`,c=d?`--clamp:${e.clamp}`:"";return s`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?s`<div class=${u} ref=${t} style=${c}>
          ${(e.text??"").split(/\n{2,}/).map($=>s`<p>${$}</p>`)}
        </div>`:s`<div class=${u} ref=${t} style=${c} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(l||r)?s`<button type="button" class="link more" onClick=${()=>o(!r)}>${r?"less":"more"}</button>`:null}
  </div>`}function pe(e){let[t,n]=h(!!e.startEditing),[a,r]=h(e.value),[o,l]=h(null),[i,d]=h(null),u=B(null),c=B(!1);M(()=>l(null),[e.value]),M(()=>{!t||!u.current||(u.current.focus(),e.startEditing?u.current.select():u.current.setSelectionRange(u.current.value.length,u.current.value.length))},[t]);let[$,p]=h(!1),f=e.locked??void 0,E=b=>{if(!b.target.closest("a, button, input, summary")){if(f)return p(!0);b.preventDefault(),r(o??e.value),d(null),c.current=!1,n(!0)}},C=()=>{c.current=!0,n(!1),d(null),e.onCancel?.()},y=async()=>{if(c.current)return;c.current=!0;let b=e.multiline?a.trim():a.replace(/\s*\n\s*/g," ").trim();if(b===e.value.trim()||!b&&!e.multiline)return C();n(!1),l(b);try{await e.onSave(b)}catch(g){l(null),r(b),d(g.message),c.current=!1,n(!0)}},S=b=>{if(b.key==="Escape")return b.preventDefault(),b.stopPropagation(),C();b.key!=="Enter"||b.isComposing||b.keyCode===229||(!e.multiline||b.metaKey||b.ctrlKey)&&(b.preventDefault(),y())};if(t)return s`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${u} class="edit-field" value=${a} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,a.split(`
`).length+1)):1}
        onInput=${b=>r(b.target.value)} onKeyDown=${S} onBlur=${y}></textarea>
      <span class="edit-hint">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${i?s` · <span class="bad-text">${i}</span>`:null}</span>
    </div>`;let m=o??e.value;return s`<div class=${`editable${f?" locked":""}${o!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${f?`${e.label}: ${f}`:`Edit ${e.label}`}
      data-tip=${f} onClick=${E} onBlur=${()=>p(!1)}
      onKeyDown=${b=>b.key==="Enter"&&b.target===b.currentTarget&&E(b)}>
    ${m.trim()?e.render?e.render(m):m:s`<span class="subtle">${e.placeholder??"Click to write"}</span>`}
    ${$&&f?s`<span class="edit-hint locked-why" role="status"><${v} name="lock" size=${12} /> ${f}</span>`:null}
  </div>`}function mt(e){let t=[];if(e.effect!==void 0&&e.effect!==null){let n=e.ci?` [${G(e.ci[0])}, ${G(e.ci[1])}]`:"";t.push(`${e.effect>=0?"+":""}${G(e.effect)}${n}`)}return e.threshold!==void 0&&e.threshold!==null&&t.push(`needs ${e.op} ${G(e.threshold)}`),e.points&&t.push(`${e.points} point${e.points>1?"s":""}`),e.detail&&t.push(e.detail),t.join(" \xB7 ")}function pt(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function Nn({node:e}){let t=te("proposal"),n=te("check"),a=t.data,r=n.data;if(!a)return s`<${ee} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let o=a.proposal??{},l=(a.versions??[]).filter(d=>d.version!==a.version),i=!e.props.of||e.props.of===".";return s`<${ee} title="Predictions" result=${t} class="proposal-block">
    ${i?null:s`<p class="statement">${o.statement}</p>`}
    ${o.rationale?s`<p class="rationale">${o.rationale}</p>`:null}
    <div class="predictions">
      ${(r?.predictions??[]).map(d=>s`<div class="prediction" key=${d.name}>
          <${T} spec=${D("result",d.result)} />
          <span class="pname">${d.name}</span>
          <span class="pdetail num">${mt(d)}</span>
        </div>`)}
    </div>
    ${l.length?s`<${at} summary=${`${l.length} earlier version${l.length>1?"s":""}`}>
          ${l.map(d=>s`<p class="small"><code>${d.version}</code> ${d.statement}
            <span class="muted">(${d.runs} runs, check ${d.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function _n({node:e}){let t=te("main"),n=e.data?.main.params.group??".",a=t.data?.chain??[],r=a.find(i=>i.group===n)??null,o=a.filter(i=>i.group!==n),l=r?.notes_since?"out of date":r?`version ${r.versions??1}`:"none yet";return s`<${st} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?l:void 0} open=${!1} result=${t} class="memory-block"
      action=${s`<${T} spec=${{icon:"circle-help",tone:"muted",label:ys}} />`}>
    <${pe} value=${r?.body??""} label="the memory" multiline class="markdown"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${i=>s`<${Ye} text=${i} />`} onSave=${i=>cn(n,i)} />
    ${r&&(r.body?.length>(t.data?.budget??1/0)||r.notes_since>=bs)?s`<p class="memory-meta warn-text">${r.body?.length>t.data.budget?`${r.body.length} characters, beyond the budget of ${t.data.budget}`:`${r.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${r?s`<p class="memory-meta">${r.author} · covers notes until ${r.covers_until?.slice(0,10)}
          ${r.notes_since?s` · <span class="warn-text">${r.notes_since} newer note${r.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${o.length?s`<p class="memory-meta">Memory above this group: ${o.map((i,d)=>s`${d?", ":""}<a href=${k(i.group)}>${i.group==="."?"local":i.group}</a>`)}</p>`:null}
  <//>`}var bs=5,ys="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",ws="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function Rn({node:e}){let t=te("main"),n=e.data?.main.params.from??".",a=P(t.data).filter(r=>r.path!==n);return s`<${ee} title=${e.props.title} count=${t.data?String(a.length):void 0} result=${t}>
    ${t.data&&!a.length?s`<${z}>No groups below.<//>`:null}
    <div class="group-list">
      ${a.map(r=>{let[o,l]=pt(r.progress),i=(r.failed??0)+(r.killed??0)+(r.lost??0);return s`<a class="group-row" key=${r.path} href=${k(r.path)}
            onPointerEnter=${()=>Oe(r.path)} onFocus=${()=>Oe(r.path)}>
          <${T} spec=${D("research",r.status)} />
          <span class="gname">${r.path.split("/").pop()}</span>
          <span class="gfacts">
            ${r.check?s`<${T} spec=${D("result",r.check)} word />`:null}
            ${r.verdict?s`<${T} spec=${D("verdict",r.verdict)} />`:null}
            ${o?s`<span data-tip=${l}>${o}</span>`:null}
            <span class="num"><b>${r.runs}</b> runs</span>
            ${r.running?s`<${T} spec=${D("run","running")} />`:null}
            ${i?s`<span class="tone-bad num" data-tip="failed, killed or lost"><${v} name="circle-x" size=${14} /> ${i}</span>`:null}
          </span>
          ${r.proposal?s`<span class="gstatement">${r.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function Ln({node:e}){let t=te("main"),n=e.data?.main.params.from??".",[a,r]=h(!1),o=(t.data?.entries??[]).filter(i=>!String(i.state??"").startsWith("superseded")),l=t.data?.meta?.matched??o.length;return s`<${st} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(l):void 0} result=${t}
      action=${s`<${T} spec=${{icon:"circle-help",tone:"muted",label:ws}} />
        ${s`<${K} icon="plus" label="Add a note" onClick=${()=>r(!0)} />`}`}>
    <div class="notes">
      ${a?s`<${Es} group=${n} onDone=${()=>r(!1)} />`:null}
      ${t.data&&!o.length&&!a?s`<p class="muted small">No notes yet.</p>`:null}
      ${o.map(i=>s`<${Je} key=${i.id} note=${i} scope=${n} />`)}
      ${t.data?.more&&e.data?s`<${Pn} call=${e.data.main} before=${o[o.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var ks=20;function Pn(e){let[t,n]=h(!1),a=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:ks}}:null,r=w(a);if(!t)return s`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(r.status==="error")return s`<p class="bad-text small">${r.error}</p>`;let o=r.data?.entries??[];return s`${r.data?null:s`<div class="skeleton" style="block-size: 40px"></div>`}
    ${o.map(l=>s`<${Je} key=${l.id} note=${l} scope=${e.scope} />`)}
    ${r.data?.more?s`<${Pn} call=${e.call} before=${o[o.length-1]?.id} scope=${e.scope} />`:null}`}var xs=["observation","idea","question","decision"];function Es(e){let[t,n]=h("observation"),[a,r]=h(""),[o,l]=h(""),[i,d]=h(null),[u,c]=h(!1),$=async f=>{if(f.preventDefault(),!a.trim())return d("give the note a title");c(!0);try{await ln(e.group,t,a.trim(),o.trim()),e.onDone()}catch(E){d(E.message),c(!1)}};return s`<form class="note new-note" onSubmit=${$} onKeyDown=${f=>{f.key==="Escape"&&e.onDone(),f.key==="Enter"&&(f.metaKey||f.ctrlKey)&&$(f)}}>
    <div class="note-line">
      <select class="note-type" value=${t} aria-label="Note type" onChange=${f=>n(f.target.value)}>
        ${xs.map(f=>s`<option value=${f}>${f}</option>`)}
      </select>
      <input class="new-note-title" value=${a} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${f=>r(f.target.value)} />
    </div>
    <textarea class="new-note-body" rows="4" value=${o} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${f=>l(f.target.value)}></textarea>
    <div class="save-actions">
      <button type="submit" class="button primary" disabled=${u}>${u?"Adding\u2026":"Add note"}</button>
      <button type="button" class="link small" onClick=${e.onDone}>cancel</button>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${i?s`<span class="bad-text small">${i}</span>`:null}
    </div>
  </form>`}function Je(e){let t=e.note,[n,a]=h(!!e.open),[r,o]=h(!1),l=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,i=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),d=t.meta?.author;return s`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${u=>!u.target.closest(".editable, a, .note-delete")&&a(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${v} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${T} spec=${D("note",t.type)} />
      <${pe} value=${t.description} label="the note's title" class="note-title" render=${Ts}
        onSave=${u=>lt(t,{description:u})} />
      ${t.overall?s`<${T} spec=${D("verdict",t.overall)} />`:null}
      ${t.state?s`<span class="tag tone-warn">${t.state}</span>`:null}
      ${l?s`<a class="note-group" href=${k(l)} data-tip="from this group">${Ss(l,e.scope)}</a>`:null}
      <span class="note-meta">${d?`${d} \xB7 `:""}${A(i)}</span>
      ${s`<${K} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${r}
        onClick=${u=>{u.stopPropagation(),o(!r)}} />`}
    </div>
    ${r?s`<div class="note-confirm" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <button type="button" class="button danger" onClick=${()=>{dn(t)}}>Delete</button>
          <button type="button" class="link small" onClick=${()=>o(!1)}>cancel</button>
        </div>`:null}
    ${n?s`<${pe} value=${t.body??""} label="the note" multiline class="note-body markdown"
          placeholder="Add details in Markdown" render=${u=>s`<${Ye} text=${u} />`}
          onSave=${u=>lt(t,{body:u})} />`:null}
  </article>`}function Ss(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,a=n.split("/").pop()??n;return ve(a)?a.slice(-8):n}function On({node:e}){let t=te("main"),n=t.data?.lines??[],a=t.data?.meta??{},r=s`<${v} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${a.total_lines??n.length} lines${(a.shown??0)<(a.total_lines??0)?`, last ${a.shown}`:""}`:""}</span>`;return s`<${ee} result=${t}>
    <${at} summary=${r} open=${e.props.open}>
      <pre class="log">${n.join(`
`)}</pre>
    <//>
  <//>`}function In({node:e}){let t=me(Y);return s`<${ee} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${pe} value=${e.props.text??""} label="the text" multiline class="markdown"
      startEditing=${ke.value===e.id} onCancel=${()=>ke.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>s`<${Ye} text=${n} />`}
      onSave=${n=>(ke.set(null),We(t.path,e.id,n))} />
  <//>`}function zn({node:e}){return s`<${z} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function Ts(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let a=n.slice(2,-2),[r]=a.split(/[#@]/),o=r.split("/").pop()??"";return s`<a href=${ve(o)?re(o):k(r)}>${a}</a>`}return n.startsWith("`")?s`<code>${n.slice(1,-1)}</code>`:n})}function Bn(e){let t=()=>R(k(e.path),{replace:!0});return s`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head">
      <span class="status-item"><${v} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${K} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?s`<${Cs} id=${e.run} scope=${e.path} />`:s`<${Ms} path=${e.path} />`}
  </aside>`}function Cs({id:e,scope:t}){let n=w(Xe(e,t)).data,a=w(yn(e,t)).data,r=w(Pe(t)).data,o=ne(),l=Te(()=>Ue(P(r).map(u=>u["run.id"]),o).get(e),[r,o,e]);if(!n)return s`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let i=n.run,d=Object.entries(n.metrics??{});return s`<div class="drawer-body">
    <h3><span class="run-dot" style=${`background:${l??"var(--bt-subtle)"}`}></span>
      <a href=${re(e)}>${i.name}</a></h3>
    <p class="facts small">
      <${T} spec=${D("run",i.status)} word />
      <span class="fact"><b>${fe(i.steps)}</b> steps</span>
      <span class="fact"><b>${ye(i.duration_s)}</b></span>
      <span class="fact" data-tip=${i.created_at}>${A(i.created_at)}</span>
    </p>
    ${i.error?s`<pre class="log bad-text">${i.error}</pre>`:null}
    <h4>Config</h4>
    <table class="kv">${Object.entries(n.config??{}).map(([u,c])=>s`<tr><td>${u}</td><td class="num">${G(c)}</td></tr>`)}</table>
    ${d.length?s`<h4>Metrics</h4>
          <table class="kv">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${d.map(([u,c])=>s`<tr><td>${u}</td><td class="num"><b>${G(c.last)}</b></td>
              <td class="num">${G(c.min)}</td><td class="num">${G(c.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?s`<h4>Cited by</h4>${n.cited_by.map(u=>s`<p class="small"><${T} spec=${D("note",u.type)} /> ${u.description}</p>`)}`:null}
    <h4>Events</h4>
    ${(n.events??[]).slice(-8).map(u=>s`<div class="event"><span class="muted num">${u.t?.slice(5,16).replace("T"," ")}</span>
        <${v} name=${rt(u.type)} size=${14} /><span>${u.description}</span></div>`)}
    <h4>Output</h4>
    <pre class="log">${(a?.lines??[]).join(`
`)}</pre>
  </div>`}function Ms({path:e}){let t=w(wn(e)).data,n=w(kn(e)).data;return s`<div class="drawer-body">
    <h4 style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?s`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(a=>!String(a.state??"").startsWith("superseded")).map(a=>s`<${Je} key=${a.id} note=${a} />`)}</div>
    <h4>Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(a=>s`<div class="event"><span class="muted num">${a.t?.slice(5,16).replace("T"," ")}</span>
        <${v} name=${a.kind==="note"?"file-text":rt(a.type)} size=${14} />
        <span>${a.run?s`<a href=${re(a.run)}>${a.run.slice(-8)}</a> `:null}${a.description??a.type}</span></div>`)}
  </div>`}var $t=["failed","killed","lost"];function ft(e){let t=Be(e.path),n=t==="."?e.path:e.path.slice(t.length+1),a=q(e.path)?[]:n.split("/"),r=a.length&&ve(a[a.length-1])?a[a.length-1]:null,o=a.slice(0,-1),l=i=>[...t==="."?[]:[t],...o.slice(0,i+1)].join("/");return s`<header class="header">
    <nav class="crumbs" aria-label="Breadcrumb">
      ${a.length?s`<a href=${k(t)}>${t==="."?"local":t}</a>`:null}
      ${o.map((i,d)=>s`<span class="sep">/</span><a href=${k(l(d))}>${i}</a>`)}
    </nav>
    ${r?s`<${Ns} id=${r} scope=${e.path} />`:s`<${Ds} path=${e.path} />`}
    ${e.finding?s`<p class="finding">${e.finding}</p>`:null}
  </header>`}function Ds({path:e}){let t=P(w(dt(e)).data)[0]??null,n=w(t?.proposal?vn(e):null).data,a=w(t?.proposal?bn(e):null).data,r=a?.proposal?.rationale,o=a?.versions?.find(c=>c.version===a.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,l=e==="."?"local":e.split("/").pop();if(!t)return s`<h1 class="title" tabindex="-1">${l}</h1><div class="skeleton late" style="block-size: 52px"></div>`;let[i,d]=pt(n?.progress?.text??t.progress),u=$t.reduce((c,$)=>c+(t[$]??0),0);return s`
    <h1 class="title" tabindex="-1">${l} <${T} spec=${D("research",t.status)} word /></h1>
    ${t.proposal?s`<div class="statement">
          <${pe} value=${t.proposal} label="the proposal's statement" locked=${a?o:"Loading the proposal\u2026"}
            render=${c=>s`<span data-tip=${o?void 0:r}>${c}</span>`}
            onSave=${c=>un(e,c)} />
        </div>`:null}
    ${t.proposal?s`<div class="preds">
          ${(n?.predictions??[]).map(c=>s`<span class="pred" key=${c.name} data-tip=${mt(c)}>
              <${T} spec=${D("result",c.result)} /><b>${c.name}</b></span>`)}
          ${n?.provisional?s`<span class="tag tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
          ${i?s`<span class="pred"><${zt} fraction=${n?.progress?.fraction??null} label=${d??i} />
                <span data-tip=${d}>${i}</span></span>`:null}
          ${t.verdict?s`<span class="pred"><${T} spec=${D("verdict",t.verdict)} word /></span>`:null}
        </div>`:null}
    <div class="facts">
      <span class="fact"><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?s`<span class="fact"><${T} spec=${D("run","running")} /><b>${t.running}</b> running</span>`:null}
      ${t.finished?s`<span class="fact"><${T} spec=${D("run","finished")} /><b>${t.finished}</b> finished</span>`:null}
      ${u?s`<span class="fact tone-bad" data-tip=${$t.filter(c=>t[c]).map(c=>`${t[c]} ${c}`).join(", ")}>
            <${v} name="circle-x" size=${15} /><b class="tone-bad">${u}</b> ${u===1?$t.find(c=>t[c]):"ended early"}</span>`:null}
      ${t.notes?s`<span class="fact"><${v} name="file-text" size=${15} /><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${Hn} path=${e} />
    </div>`}function Ns({id:e,scope:t}){let n=w(Xe(e,t)).data;if(!n)return s`<h1 class="title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 52px"></div>`;let a=n.run,r=()=>{navigator.clipboard?.writeText(a.id)};return s`
    <h1 class="title" tabindex="-1"><${pe} value=${a.name??a.id} label="the run's name" class="title-edit"
        onSave=${o=>mn(a.id,t,o.trim())} />
      <${T} spec=${D("run",a.status)} word /></h1>
    ${a.error?s`<p class="statement bad-text" data-tip=${a.error}>${a.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span class="fact"><b>${fe(a.steps)}</b> steps</span>
      <span class="fact"><b>${ye(a.duration_s)}</b></span>
      <span class="fact" data-tip=${a.created_at}>${A(a.created_at)}</span>
      <${Hn} path=${t} />
      <span class="fact">
        <${K} icon="copy" label=${`Copy the run id ${a.id}`} onClick=${r} />
        <${Bt} icon="ellipsis" label="Details" title="Run details" class="run-details">
          <table class="kv">${_s(a).map(([o,l])=>s`<tr><td class="muted">${o}</td><td>${l}</td></tr>`)}</table>
          <div class="menu-list">
            <button type="button" onClick=${()=>R(k(t,{run:a.id}),{replace:!0})}>
              <${v} name="panel-right" size=${15} /> Open in the side panel</button>
            <button type="button" onClick=${r}><${v} name="copy" size=${15} /> Copy the run id</button>
            ${a.git?.commit?s`<button type="button" onClick=${()=>navigator.clipboard?.writeText(a.git.commit)}>
              <${v} name="git-commit" size=${15} /> Copy the commit</button>`:null}
          </div>
        <//>
      </span>
    </div>
    ${(n.proposals??[]).length?s`<div class="preds" style="margin-block-start: 10px">
          ${n.proposals.map(o=>s`<a class="pred" href=${k(o.group)} data-tip=${o.statement}>
              <${T} spec=${D("result",o.check)} /><b>${o.group==="."?"own proposal":o.group}</b>
              ${o.verdict?s`<${T} spec=${D("verdict",o.verdict)} />`:null}</a>`)}
        </div>`:null}`}function Hn({path:e}){let t=w(ut(e)).data?.summary;if(!t)return null;let n=Object.entries(t.config??{}).map(([r,o])=>`${r} ${G(o)}`).join(", "),a=ve(e.split("/").pop()??"");return s`<span class="fact" data-tip=${`${t.stat} of ${t.metric} over ${a?"the run":"all runs"}`}>
    best <b>${t.metric} ${G(t.value)}</b>
    ${a?null:s`<span>· <a href=${re(t.run)}>${t.name}</a>${n?s` <em>(${n})</em>`:null}</span>`}
  </span>`}function _s(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,a])=>[n,String(a)])}var An=15e3;function Un({node:e}){let t=me(Y),n=ne(),[a,r]=Pt(),o=e.props.code,l=w(r&&o?{method:"code",params:o,scope:t.path}:null),[i,d]=h(null),[u,c]=h(120),[$,p]=h({error:null,warnings:[]}),f=y=>{oe&&console.error(`[block ${e.id}] ${y}`),p(S=>({...S,error:y}))};M(()=>{let y=i?.contentWindow;if(!y||l.status!=="ready")return;let S=I=>y.postMessage(I,"*"),m=new Map,b=new Vt,g=!0;De.n++;let O=()=>{g&&De.n--,g=!1},j=setTimeout(()=>{g&&f(`no first render within ${An/1e3} s`),O()},An),U=I=>{if(I.source!==y)return;let x=I.data;switch(x.type){case"hello":S({type:"init",init:{id:e.id,code:l.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:Lt.value,pair:He.value,prefs:ot(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics}});break;case"sub":if(!Ft.has(x.call.method)){S({type:"result",id:x.id,result:{status:"error",data:null,error:`${x.call.method} is not available in a custom block`,refreshing:!1}});break}m.get(x.id)?.(),m.set(x.id,xt(x.call,Se=>S({type:"result",id:x.id,result:Se})));break;case"unsub":m.get(x.id)?.(),m.delete(x.id);break;case"navigate":x.url.startsWith("/")&&R(x.url);break;case"height":b.accept(performance.now())?c(Math.max(40,x.height)):L("its height keeps changing, so it is fixed at its last height");break;case"ready":p(Se=>({...Se,blank:x.blank,overflow:x.overflow})),O();break;case"warn":L(x.message);break;case"hover":tt.set(x.run);break;case"prefs":JSON.stringify(N.value)!==JSON.stringify(x.prefs)&&N.set(x.prefs);break;case"download":case"snapshot":x.href?Wt(x.href,x.name)?performance.now()-F>1e3&&(F=performance.now(),Le().download(x.href,x.name)):L(`a download of ${x.name} was refused: only PNG, SVG and CSV files`):L("it draws no SVG or canvas to download");break;case"figure":Le().figure(x.spec,x.name).catch(Se=>L(`the PDF failed: ${Se.message}`));break;case"expand":Gt(x.node)&&Le().expand(x.node,t);break;case"error":f(x.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,E)),O();break;default:break}},L=I=>{oe&&console.warn(`[block ${e.id}] ${I}`),p(x=>x.warnings.includes(I)?x:{...x,warnings:[...x.warnings,I]})},F=0,N=ot(t.path),Z=tt.subscribe(I=>S({type:"hover",run:I})),de=N.subscribe(I=>S({type:"prefs",prefs:I}));return addEventListener("message",U),S({type:"ping"}),()=>{Z(),de(),removeEventListener("message",U),clearTimeout(j);for(let I of m.values())I();O()}},[l.status,l.data,i]),M(()=>{let y={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};i?.contentWindow?.postMessage(y,"*")},[t.names,t.colors,t.metrics,i]),M(()=>{n&&i?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let E=typeof o=="object"?o.path??o.block:String(o??"");Ot(e.id,{png:()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")});let C=r&&l.status==="ready"&&!$.error;return s`<div ref=${a} class="custom-block">
    <div class="chart-head">
      <span class="chart-title">${e.props.title??""}</span>
      ${C?s`<span class="chart-tools">
            <${K} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?s`<${K} icon="x" label="Close (Esc)" onClick=${()=>Re.set(null)} />`:s`<${K} icon="maximize" label="Expand" onClick=${()=>Le().expand(e,t)} />`}
          </span>`:null}
    </div>
    <${ee} caption=${e.props.expanded?void 0:e.props.caption} result=${l}>
      ${$.error?s`<div class="notice error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${E})</span>
            <pre>${$.error}</pre>
          </div>`:null}
      ${$.warnings.map(y=>s`<${z} kind="warning">${y}<//>`)}
      ${C?s`<div class="custom-frame" data-frame-blank=${$.blank?"1":void 0} data-frame-overflow=${$.overflow?"1":void 0}>
            <iframe key=${l.data.code} ref=${d} sandbox="allow-scripts" ...${Rs()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${u}px`} />
          </div>`:null}
    <//>
  </div>`}function Rs(){if(!!1)return{src:wt("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1"),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame"><div id="root"></div><script>${n}<\/script></body></html>`}}function Kn({node:e}){let t=te("main"),n=me(Y),a=t.data?.entries??[];return s`<${ee} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!a.length?s`<${z}>No images logged.<//>`:null}
    <div class="images">
      ${a.map(r=>s`<figure key=${`${r.run}/${r.path}`}>
          <img src=${kt(Ne(r.run,n.path),r.path)} alt=${r.caption??e.props.title} loading=${_e?"eager":"lazy"} />
          <figcaption>step ${fe(r.step)}${r.caption?` \xB7 ${r.caption}`:""}</figcaption>
        </figure>`)}
    </div>
  <//>`}function jn({node:e}){let t=te("main"),n=t.data?.entries??[];return s`<${ee} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?s`<${z}>No text logged.<//>`:null}
    ${n.map(a=>s`<div class="text-entry" key=${`${a.run}/${a.step}`}>
        <div class="muted small">step ${fe(a.step)}${a.caption?` \xB7 ${a.caption}`:""}</div>
        <pre>${a.text??""}</pre>
      </div>`)}
  <//>`}function Fn({node:e}){let[t,n]=h(_e||e.props.open!==!1),a=s`${(e.children??[]).map(r=>s`<${ae} key=${r.id} node=${r} />`)}`;return e.props.title?s`<section class="section">
    <button type="button" class="section-title" aria-expanded=${t} onClick=${()=>n(!t)}>
      <${v} name=${t?"chevron-down":"chevron-right"} size=${16} />${e.props.title}
    </button>
    ${t?s`<div class="stack">${a}</div>`:null}
  </section>`:s`<div class="stack">${a}</div>`}function Wn({node:e}){return s`<div class="row">
    ${(e.children??[]).map(t=>s`<${ae} key=${t.id} node=${t} />`)}
  </div>`}function Gn({node:e}){let t=me(Y),n=je(t.path),a=e.props.min_width??320,r=e.props.columns,o=r?`grid-template-columns: repeat(${r}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${a}px, 100%), 1fr))`,l=(e.children??[]).flatMap(c=>c.props.y??[]),i=e.props.addable?n.added.filter(c=>!l.includes(c)).map(c=>({block:"line",id:`added-${c}`,props:{y:c,added:!0},data:{main:{...e.props.template,params:{...e.props.template.params,y:[c]}}}})):[],d=jt([...e.children??[],...i],n.order[e.id]),u=(c,$)=>{let p=d.map(f=>f.id).filter(f=>f!==c);p.splice(p.indexOf($),0,c),Ut(t.path,e.id,p)};return s`<div class="grid" style=${o}>
    ${d.map(c=>s`<${Ls} key=${c.id} node=${c} path=${t.path} span=${n.spans[c.id]??c.props.span??1}
      columns=${r} onDrop=${$=>$!==c.id&&u($,c.id)} />`)}
    ${e.props.addable&&!!1?s`<${Ps} path=${t.path} shown=${[...l,...n.added]} />`:null}
  </div>`}var ht=[1,2,"full"];function Ls(e){let[t,n]=h(!1),a=ht[(ht.indexOf(e.span)+1)%ht.length],r=o=>o==="full"?"full width":`${o} column${o===1?"":"s"}`;return s`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${o=>{o.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${o=>{o.preventDefault(),n(!1),e.onDrop(o.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${o=>o.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${v} name="grip" size=${14} /></span>
      <button type="button" class="cell-width" data-tip=${`Width: ${r(e.span)}; click for ${r(a)}`}
        aria-label=${`Width ${r(e.span)}`} onClick=${()=>Kt(e.path,e.node.id,a)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${ae} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function Ps(e){let t=w({method:"keys",params:{from:e.path},scope:e.path}).data,n=(t?.metrics?.rows??[]).map(a=>a[0]).filter(a=>!e.shown.includes(a));return t&&!n.length?null:s`<div class="add-chart">
    <span class="add-chart-label"><${v} name="plus" size=${16} /> Add a chart</span>
    <${Ke} single options=${n} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
      onChange=${([a])=>Fe(e.path,r=>({added:[...r.added,a]}))} />
  </div>`}function Vn({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[a,r]=h(()=>t.find(i=>i.id===n())?.id??t[0]?.id),o=i=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(i)}`),r(i)},l=t.find(i=>i.id===a)??t[0];return _e?s`<div class="stack">${t.map(i=>s`<${ae} key=${i.id} node=${i} />`)}</div>`:s`<div class="tabs">
    <div class="tab-list" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(i=>s`<button type="button" role="tab" id=${`tab-${i.id}`} aria-selected=${i.id===l?.id}
          aria-controls=${`panel-${i.id}`} onClick=${()=>o(i.id)}>${i.props.title??i.id}</button>`)}
    </div>
    ${l?s`<div class="stack" role="tabpanel" id=${`panel-${l.id}`} aria-labelledby=${`tab-${l.id}`}>
          ${(l.children??[]).map(i=>s`<${ae} key=${i.id} node=${i} />`)}
        </div>`:null}
  </div>`}var Os={section:Fn,row:Wn,grid:Gn,line:en,table:rn,stat:an,images:Kn,text:jn,proposal:Nn,note:zn,output:On,memory:_n,groups:Rn,notes:Ln,tabs:Vn,scatter:tn,bar:nn,histogram:sn,data_table:Yt,timeline:Jt,custom:Un,markdown:In};function ae({node:e}){return s`<${Ht} node=${e} blocks=${Os} />`}function Xn(e,t){let n=e.split(`
`),a=t.split(`
`),r=n.length,o=a.length,l=Array.from({length:r+1},()=>new Uint32Array(o+1));for(let c=r-1;c>=0;c--)for(let $=o-1;$>=0;$--)l[c][$]=n[c]===a[$]?l[c+1][$+1]+1:Math.max(l[c+1][$],l[c][$+1]);let i=[],d=0,u=0;for(;d<r&&u<o;)n[d]===a[u]?(i.push({kind:"same",text:n[d]}),d++,u++):l[d+1][u]>=l[d][u+1]?i.push({kind:"removed",text:n[d++]}):i.push({kind:"added",text:a[u++]});for(;d<r;)i.push({kind:"removed",text:n[d++]});for(;u<o;)i.push({kind:"added",text:a[u++]});return i}function qn(e,t=3){let n=[],a=0;for(;a<e.length;){if(e[a].kind!=="same"){n.push(e[a++]);continue}let r=a;for(;r<e.length&&e[r].kind==="same";)r++;let o=a===0?0:t,l=r===e.length?0:t;r-a>o+l+1?n.push(...e.slice(a,a+o),{kind:"skip",count:r-a-o-l},...e.slice(r-l,r)):n.push(...e.slice(a,r)),a=r}return n}function Ze(e){let t=w(Pe(e.path)),n=ne(),a=P(t.data),r=Te(()=>Ue(a.map(i=>i["run.id"]),n),[t.data,n]),o=Te(()=>new Map(a.map(i=>[i["run.id"],i["run.name"]??i["run.id"]])),[t.data]);if(!e.view)return s`<div class="view"><div class="skeleton late" style="block-size: 320px"></div></div>`;let l={path:e.path,colors:r,names:o,metrics:e.view.metrics??{}};return s`<div class="view"><${Y.Provider} value=${l}><${ae} node=${e.view.view} /><//></div>`}function Yn(e){if(null)return s`<div class="view-source"><${v} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=_(W),a=n.page==="group"&&n.version,r=t.versions?s`<a href=${k(e.path,{history:!0})}><${v} name="history" size=${14} /> history (${t.versions})</a>`:null,o;switch(t.source){case"draft":o=s`draft <b>${t.draft}</b>`;break;case"view":o=s`${t.title?s`<em>${t.title}</em> · `:null}saved ${A(be(t.version))} by ${t.author??"unknown"}`;break;default:o=s`the built-in view`}return s`<div class="view-source">
    <${v} name="layout" size=${14} /><span>${o}</span>
    ${a?s`<a href=${k(e.path)}>an older version · show the current one</a>`:null}
    ${r}
    ${t.outdated?.length&&!a?s`<${Is} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||a?null:s`<${zs} path=${e.path} />
        <${Bs} path=${e.path} view=${t} />`}
  </div>`}function Is(e){let[t,n]=h(null),a=e.outdated.map(o=>o.name).join(", ");return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{await pn(e.path)}catch(o){n(o.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${a} exists; update re-pins this view to it (a new version)`}>
      <${v} name="update" size=${14} /> update ${a}</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function zs(e){let[t,n]=h(null);return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{ke.set(await We(e.path,null,""))}catch(r){n(r.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${v} name="file-text" size=${14} /> add text</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function Bs(e){let t=je(e.path),n=At(t),[a,r]=h(!1),[o,l]=h(e.view.title??""),[i,d]=h(e.view.finding??""),[u,c]=h(null),[$,p]=h(!1);if(!n&&!a)return null;let f=async E=>{E.preventDefault(),p(!0),c(null);try{let C={charts:t.charts,added:t.added,order:t.order,spans:t.spans};await H("save_view",{path:e.path,prefs:C,title:o,finding:i}),Fe(e.path,()=>({view:{},charts:{},added:[],order:{},spans:{}})),ge(y=>["view","view_history","summary"].includes(y.method)&&y.scope===e.path),r(!1)}catch(C){c(C.message)}finally{p(!1)}};return a?s`<form class="save-form" onSubmit=${f}>
    <label class="field"><span class="field-label">Title</span>
      <input value=${o} onInput=${E=>l(E.target.value)} /></label>
    <label class="field"><span class="field-label">Finding</span>
      <input value=${i} placeholder="the key result in one sentence"
        onInput=${E=>d(E.target.value)} /></label>
    <div class="save-actions">
      <button type="submit" class="button primary" disabled=${$}>${$?"Saving\u2026":"Save as view"}</button>
      <button type="button" class="link small" onClick=${()=>r(!1)}>cancel</button>
      ${u?s`<span class="bad-text small">${u}</span>`:null}
    </div>
  </form>`:s`<button type="button" class="link small save-view" onClick=${()=>r(!0)}
        data-tip="Save your chart settings and added charts as this page's view, for everyone">
      <${v} name="save" size=${14} /> Save as view</button>`}function Jn(e){let t=w(Sn(e.path)),n=t.data?.entries??[],[a,r]=h(null),o=a??n.slice(0,2).map(i=>i.version).reverse(),l=i=>{let d=o.includes(i)?o.filter(u=>u!==i):[...o,i].slice(-2);r(d.sort())};return t.status==="error"?s`<${z} kind="error">${t.error}<//>`:s`<section class="history">
    <h2 class="history-title"><${v} name="history" size=${18} /> View history</h2>
    ${t.data&&!n.length?s`<${z}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((i,d)=>s`<li key=${i.version} class=${o.includes(i.version)?"picked":""}>
          <label><input type="checkbox" checked=${o.includes(i.version)} onChange=${()=>l(i.version)} />
            <span class="num muted" data-tip=${i.version}>${A(i.time)}</span>
            <b>${i.title??"untitled"}</b><span class="muted">${i.author??""}</span>
            ${i.message?s`<span>${i.message}</span>`:null}</label>
          <a href=${d===0?k(e.path):k(e.path,{version:i.version})}
            onClick=${u=>{u.preventDefault(),R(d===0?k(e.path):k(e.path,{version:i.version}))}}>${d===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${o.length===2?s`<${Hs} path=${e.path} a=${o[0]} b=${o[1]} />`:null}
  </section>`}function Hs(e){let t=i=>({method:"view_show",params:{group:e.path,version:i},scope:e.path}),n=w(t(e.a)).data,a=w(t(e.b)).data,r=w(ce(e.path,e.a)).data,o=w(ce(e.path,e.b)).data,l=n&&a?qn(Xn(n.yaml,a.yaml)):[];return s`<div class="compare">
    <h3 class="block-title">Changes from ${A(be(e.a))} to ${A(be(e.b))}</h3>
    <pre class="diff">${l.map(i=>i.kind==="skip"?s`<div class="diff-skip">⋯ ${i.count} unchanged lines</div>`:s`<div class=${`diff-${i.kind}`}>${i.kind==="added"?"+ ":i.kind==="removed"?"\u2212 ":"  "}${i.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title">${r?.title??e.a}</h3><${Ze} path=${e.path} view=${r} /></div>
      <div><h3 class="block-title">${o?.title??e.b}</h3><${Ze} path=${e.path} view=${o} /></div>
    </div>
  </div>`}function Zn(e){return M(()=>{document.title=`${e.path==="."?"local":e.path} \xB7 Beamtime`},[e.path]),e.history?s`<div class="page"><${ft} path=${e.path} /><${Jn} path=${e.path} /></div>`:s`<div class="page">
    <${As} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function As(e){let t=w(ce(e.path,e.version,e.draft));return M(()=>{t.status==="ready"&&requestAnimationFrame(Mt)},[t.status==="ready"]),s`
    <${ft} path=${e.path} finding=${t.data?.finding} />
    ${t.data?s`<${Yn} path=${e.path} view=${t.data} />`:null}
    ${t.status==="error"?Us(e.path,t.error)?s`<${z} kind="warning">${t.error} The page fills in once the remote answers again.<//>`:s`<${z} kind="error">${t.error}<//>`:s`<${Ze} path=${e.path} view=${t.data} />`}`}function Us(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function Qn(e){M(()=>{he(ce(e.id)).then(n=>R(k(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=w(ce(e.id));return t.status==="error"?s`<div class="page"><${z} kind="error">${t.error}<//></div>`:s`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var gt=20,Ee=-1,Ks=[["day",86400],["week",7*86400],["month",30*86400]];function ts(e){let t=P(w(se()).data).map(i=>i.path),n=w({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),a=w({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});M(()=>{document.title="Timeline \xB7 Beamtime"},[]);let r=Date.now()/1e3,o=P(n.data).filter(i=>i["run.created_at"]).map((i,d)=>({id:i["run.id"],name:i["run.name"]??i["run.id"],group:i["run.group"],status:i["run.status"],start:Date.parse(i["run.created_at"])/1e3,end:i["run.ended_at"]?Date.parse(i["run.ended_at"])/1e3:r,lane:d})),l=(a.data?.entries??[]).map(i=>({id:i.id,type:i.type,group:i.group,description:i.description,t:Date.parse(be(i.id))/1e3}));return s`<div class="page timeline-page">
    <header class="header">
      <h1 class="title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <label class="field inline"><span class="field-label">Group</span>
          <select value=${e.from} onChange=${i=>R(ze(i.target.value),{replace:!0})}>
            ${t.map(i=>s`<option value=${i}>${i==="."?"everything":i}</option>`)}
          </select></label>
        <span class="muted small">${o.length} runs · ${l.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header>
    ${n.status==="error"?s`<p class="notice error">${n.error}</p>`:null}
    ${n.data&&a.data?s`<${js} bars=${o} marks=${l} />`:s`<div class="skeleton late" style="block-size: 320px"></div>`}
  </div>`}function js(e){let t=ne(),n=B(null),a=[...e.bars.flatMap(y=>[y.start,y.end]),...e.marks.map(y=>y.t)],r=a.length?es(Math.min(...a),Math.max(...a)):es(Date.now()/1e3-86400,Date.now()/1e3),[o,l]=h(r),i=e.bars.length,d=Math.min(900,Math.max(160,(i+1.5)*gt+40)),c=Zt(n,Qt,t?(y=>{let S=Xt(o[0],o[1]),m=g=>String(y.colors[g]??y.colors.muted),b=g=>String(y.colors[g==="verdict"?"good":g==="decision"?"accent":g==="question"?"warn":"muted"]);return{style:Rt(y),height:d,x:{range:o,log:!1,format:g=>qt(g,S.step),splits:S.at},y:{range:[Ee-.8,i+.5],log:!1,reverse:!0,size:150,splits:i<=40?[Ee,...e.bars.map(g=>g.lane)]:[Ee],format:g=>g===Ee?"notes":Xs(e.bars[Math.round(g)]?.name??"")},draw:({ctx:g,x:O,y:j,px:U,focused:L})=>{let F=gt*.62*U;for(let N of e.bars){let Z=O(N.start),de=Math.max(3*U,O(N.end)-Z);g.fillStyle=L!==null&&L!==N.id?_t(m(N.status),.35):m(N.status),g.beginPath(),g.roundRect(Z,j(N.lane)-F/2,de,F,3*U),g.fill()}for(let N of e.marks){let Z=O(N.t),de=j(Ee),I=(L===N.id?6:4.5)*U;g.fillStyle=b(N.type),g.beginPath(),g.moveTo(Z,de-I),g.lineTo(Z+I,de),g.lineTo(Z,de+I),g.lineTo(Z-I,de),g.closePath(),g.fill()}},hit:(g,O,j,U)=>{if(Math.abs(O-U(Ee))<gt/2){let N=Vs(e.marks,Z=>Math.abs(j(Z.t)-g),8);return N?{key:N.id,rows:Ws(N)}:null}let L=Math.round((O-U(0))/(U(1)-U(0))),F=e.bars.find(N=>N.lane===L&&j(N.start)-3<=g&&g<=Math.max(j(N.end),j(N.start)+3)+3);return F?{key:F.id,rows:Fs(F)}:null},onClick:g=>{let O=e.marks.find(j=>j.id===g);O?R(k(O.group,{drawer:!0})):R(re(g))}}})(t):null,[o,e.bars,e.marks],t),$=y=>{if(!c.current)return;y.preventDefault();let S=c.current.xAt(y.clientX),m=Math.exp(y.deltaY*.0015);l(([b,g])=>vt([S-(S-b)*m,S+(g-S)*m],r))},p=B(null),f=y=>p.current={x:y.clientX,range:o},E=y=>{if(!p.current||!c.current||!(y.buttons&1))return;let S=(y.clientX-p.current.x)*c.current.xPerPixel(),[m,b]=p.current.range;Math.abs(y.clientX-p.current.x)>3&&l(vt([m-S,b-S],r))},C=Math.max(...a,Date.now()/1e3);return s`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${Ks.map(([y,S])=>s`<button type="button" role="radio" aria-checked=${Math.abs(o[1]-o[0]-S)<1}
          onClick=${()=>l(vt([C-S,C+S*.02],[Math.min(r[0],C-S),r[1]]))}>last ${y}</button>`)}
      <button type="button" role="radio" aria-checked=${o[0]===r[0]&&o[1]===r[1]} onClick=${()=>l(r)}>all</button>
    </div>
    <div class="chart" ref=${n} style=${`min-block-size:${d}px`}
      onWheel=${$} onPointerDown=${f} onPointerMove=${E} onPointerUp=${()=>p.current=null}></div>
    <p class="muted small">${Gs(t)}</p>
  </div>`}function Fs(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:A(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:ye(e.end-e.start),color:null}]}function Ws(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:A(new Date(e.t*1e3).toISOString()),color:null}]}function Gs(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function Vs(e,t,n){let a=null,r=n;for(let o of e){let l=t(o);l<r&&([a,r]=[o,l])}return a}function es(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function vt([e,t],n){let a=Math.min(n[1]-n[0],Math.max(60,t-e)),r=Math.max(n[0],Math.min(e,n[1]-a));return[r,r+a]}function Xs(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function ns(){let e=_(Re),t=B(null);if(M(()=>{let r=t.current;if(!r||!e)return;r.showModal();let o=()=>Re.set(null);return r.addEventListener("close",o),()=>r.removeEventListener("close",o)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},a=String(n.props.title??n.props.y??"Chart");return s`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${a} closedby="any">
    <${Y.Provider} value=${e.view}><${ae} node=${n} /><//>
  </dialog>`}function ss(e,t){let n=e.toLowerCase(),a=t.toLowerCase();if(!n)return 1;let r=a.indexOf(n);if(r>=0)return 100-Math.min(r,50)-a.length/100;let o=0,l=0;for(let i of a)if(i===n[o]?o++:o>0&&l++,o===n.length)return 40-Math.min(l,39);return 0}function rs(e){let[t,n]=h(e.query),[a,r]=h(0),o=B(null),l=P(w(se()).data),i=P(w(qe()).data);M(()=>{let m=o.current;m.showModal();let b=()=>X.set(null);m.addEventListener("close",b);let g=!1,O=L=>{let F=m.getBoundingClientRect();return L.clientX<F.left||L.clientX>F.right||L.clientY<F.top||L.clientY>F.bottom},j=L=>g=O(L),U=L=>g&&O(L)&&m.close();return"closedBy"in HTMLDialogElement.prototype||(m.addEventListener("pointerdown",j),m.addEventListener("pointerup",U)),()=>{m.removeEventListener("close",b),m.removeEventListener("pointerdown",j),m.removeEventListener("pointerup",U)}},[]);let d=()=>o.current?.close(),u=m=>()=>R(m),c=W.value,$=c.page==="group"?c.path:".",p=(m,b,g,O)=>({section:"Commands",label:m,detail:b,sym:{icon:g,tone:"muted",label:m},run:O}),E=[...l.map(m=>({section:"Groups",label:m.path==="."?"local":m.path,detail:`${m.runs} runs${m.proposal?` \xB7 ${m.proposal}`:""}`,sym:D("research",m.status),run:u(k(m.path))})),...i.map(m=>({section:"Runs",label:m["run.name"]??m["run.id"],detail:`${m["run.status"]} \xB7 ${m["run.path"]}`,sym:D("run",m["run.status"]),run:u(k(m["run.path"]))})),p("Theme: light","","sun",()=>Ae("light")),p("Theme: dark","","moon",()=>Ae("dark")),p("Theme: follow the system","","monitor",()=>Ae("system")),p("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),p("Show notes and timeline","i","file-text",u(k($,{drawer:!0}))),p("Show or hide the sidebar","\u2318B","panel-left",()=>V.set(!V.value)),p(Q.value?"Resume live updates":"Pause live updates","p",Q.value?"play":"pause",()=>Q.set(!Q.value)),p("Keyboard shortcuts","?","keyboard",()=>le.set(!0)),p("Settings","","settings",u("/settings/appearance"))].map(m=>({it:m,s:Math.max(ss(t,m.label),ss(t,m.detail)*.5)})).filter(m=>m.s>0).sort((m,b)=>b.s-m.s||as(m.it.section)-as(b.it.section)).slice(0,60).map(m=>m.it),C=m=>{m&&(d(),m.run())},y=m=>{if(m.key==="ArrowDown")r(Math.min(E.length-1,a+1));else if(m.key==="ArrowUp")r(Math.max(0,a-1));else if(m.key==="Enter")C(E[a]);else return;m.preventDefault()},S="";return s`<dialog class="sheet" ref=${o} aria-label="Search" closedby="any">
    <div class="palette-input"><${v} name="search" size=${18} />
      <input autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${E[a]?`pal-${a}`:void 0}
        onInput=${m=>{n(m.target.value),r(0)}} onKeyDown=${y} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${E.map((m,b)=>{let g=m.section!==S&&!t?S=m.section:null;return s`${g?s`<li class="section" role="presentation">${g}</li>`:null}
          <li id=${`pal-${b}`} class="item" role="option" aria-selected=${b===a}
              onMouseMove=${()=>r(b)} onClick=${()=>C(m)}>
            <${T} spec=${m.sym} /><span class="label">${m.label}</span><span class="detail">${m.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function as(e){return["Groups","Runs","Commands"].indexOf(e)}function Qe(e,t=[]){let n=new Map,a=(o,l={})=>({path:o,name:o==="."?"local":o.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let o of e)n.set(o.path,a(o.path,o));n.has(".")||n.set(".",a("."));for(let o of t)o.name!=="local"&&(n.has(o.name)||n.set(o.name,a(o.name)),Object.assign(n.get(o.name),{state:o.state,error:o.error}));for(let o of n.values()){if(q(o.path))continue;let l=o.path.lastIndexOf("/"),i=l<0?".":o.path.slice(0,l);(n.get(i)??n.get(Be(o.path))??n.get(".")).children.push(o)}for(let o of n.values())o.children.sort((l,i)=>l.name.localeCompare(i.name));let r=[...n.values()].filter(o=>o.path!=="."&&q(o.path)).sort((o,l)=>o.name.localeCompare(l.name));return[n.get("."),...r]}function os(e,t,n){let a=[],r=n.toLowerCase(),o=l=>{(!r||l.path.toLowerCase().includes(r)||is(l,r))&&(a.push(l),(r||t.has(l.path)||q(l.path))&&l.children.forEach(o))};return e.forEach(o),a}function is(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||is(n,t))}function ls(e,t){if(q(t))return e;let n=t.lastIndexOf("/"),a=n<0?".":t.slice(0,n),r=o=>o.path===a?o:o.children.map(r).find(l=>l)??null;return e.map(r).find(o=>o)?.children??[]}function cs(e){return q(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function us(){let e=_(W),t=w(se()),[n,a]=h(()=>new Set(Ce("open",[]))),[r,o]=h(""),l=B(null),i=e.page==="group"?e.path:null,d=Qe(P(t.data),t.data?.meta?.sources??[]),u=os(d,Js(n,i),r),c=(p,f)=>{let E=new Set(n);f??!E.has(p)?E.add(p):E.delete(p),Me("open",[...E]),a(E)};return s`<nav class="sidebar" aria-label="Groups">
    <label class="filter"><${v} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${r} aria-label="Filter groups"
        onInput=${p=>o(p.target.value)} />
    </label>
    <div class="tree" ref=${l} onKeyDown=${p=>{let f=[...l.current?.querySelectorAll("a.tree-item")??[]],E=f.indexOf(document.activeElement),C=u[E];switch(p.key){case"ArrowDown":f[Math.min(f.length-1,E+1)]?.focus();break;case"ArrowUp":f[Math.max(0,E-1)]?.focus();break;case"ArrowRight":C?.children.length&&c(C.path,!0);break;case"ArrowLeft":C&&n.has(C.path)?c(C.path,!1):C&&f[u.findIndex(y=>y.path===Ys(C.path))]?.focus();break;default:return}p.preventDefault()}} role="tree">
      ${u.map(p=>s`<${qs} key=${p.path} node=${p} current=${p.path===i}
        open=${n.has(p.path)||!!r} onToggle=${()=>c(p.path)} />`)}
    </div>
  </nav>`}function qs(e){let t=e.node,n=()=>Oe(t.path),a=t.children.length>0&&!q(t.path);return s`<a class=${`tree-item${e.current?" current":""}${t.path.startsWith("@")&&q(t.path)?" source-root":""}`} href=${k(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${a?e.open:void 0}
      style=${`padding-inline-start:${6+cs(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${r=>{r.metaKey||r.ctrlKey||(r.preventDefault(),R(k(t.path)))}}>
    <span class="twisty" onClick=${r=>{r.preventDefault(),r.stopPropagation(),e.onToggle()}}>
      ${a?s`<${v} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    <span class="tree-name">${t.name}</span>
    ${t.state==="unreachable"?s`<${T} spec=${{icon:"cloud-off",tone:"muted",label:`Unreachable: ${t.error??"no answer"}`}} size=${13} />`:null}
    <span class="tree-marks">
      ${t.running?s`<${T} spec=${D("run","running")} size=${13} />`:null}
      ${t.failed?s`<${T} spec=${{...D("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${13} />`:null}
    </span>
    <span class="count">${t.runs||""}</span>
  </a>`}function Ys(e){if(q(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function Js(e,t){if(!t||t===".")return e;let n=new Set(e),a=t.split("/");for(let r=1;r<a.length;r++)n.add(a.slice(0,r).join("/"));return n}function ms(){let e=_(W),t=_(V),n=_(X),a=_(le),r=B(null);M(()=>Ct(()=>r.current),[]),M(()=>(addEventListener("keydown",ds),()=>removeEventListener("keydown",ds)),[]);let o=e.page==="group"&&e.drawer,l;switch(e.page){case"group":l=s`<${Zn} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":l=s`<${Qn} id=${e.id} />`;break;case"settings":l=s`<${gn} />`;break;case"timeline":l=s`<${ts} key=${e.from} from=${e.from} />`;break;default:l=s`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return oe||!1?s`<main class="main render-main" ref=${r}>${l}</main>`:s`<div class=${`shell${t?"":" no-sidebar"}${o?" with-drawer":""}`}>
    <${Cn} />
    ${t?s`<${us} />`:null}
    <main class="main" ref=${r}>${l}</main>
    ${o?s`<${Bn} path=${e.path} run=${e.run} />`:null}
    <${Mn} />
    ${n!==null?s`<${rs} query=${n} />`:null}
    ${a?s`<${Qs} />`:null}
    <${ns} />
  </div>`}function ds(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),X.set(X.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),V.set(!V.value);return}if(e.key==="Escape"){if(X.value!==null||le.value)return;let a=W.value;return a.page==="group"&&a.run?R(k(a.path,{drawer:!0}),{replace:!0}):a.page==="group"&&a.drawer?R(k(a.path),{replace:!0}):void 0}if(t||e.altKey||hn(e)||X.value!==null||le.value)return;let n=W.value;switch(e.key){case"/":e.preventDefault(),X.set("");break;case"?":le.set(!le.value);break;case"p":Q.set(!Q.value);break;case"i":n.page==="group"&&R(k(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":V.set(!V.value);break;case"[":case"]":n.page==="group"&&Zs(n.path,e.key==="]"?1:-1);break}}async function Zs(e,t){let n=await he(se()),a=ls(Qe(P(n),n?.meta?.sources??[]),e),r=a.findIndex(l=>l.path===e),o=a[r+t];o&&R(k(o.path))}function Qs(){let e=B(null);return M(()=>{let t=e.current;t.showModal();let n=()=>le.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),s`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${Ge.map(([t,n])=>s`<tr><td><kbd>${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 14px"><button class="link" autofocus>Close</button></form>
    </div>
  </dialog>`}Dt();if(oe){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(ie.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>De.n,Nt&&It()}on();var ea=H("meta").then(e=>(oe&&(e={...e,settings:{...e.settings,theme_mode:ie.value}}),Ve(e),e));!oe&&!!1&&Tt(async()=>{let[e,t]=await Promise.all([ea,H("meta")]);e.bundle!==t.bundle?location.reload():Ve(t)});bt(s`<${ms} />`,document.getElementById("app"));
