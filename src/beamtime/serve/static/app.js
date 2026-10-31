import{$ as re,A as yt,Aa as nt,B as wt,Ba as He,C as fe,Ca as Ae,D as Pe,Da as Rt,E as Ye,Ea as It,F as se,Fa as Ot,G as St,Ga as zt,H as Je,Ha as Bt,I as Re,J as X,K as ee,Ka as Ht,L as te,La as At,M as Ie,Ma as Kt,N as Et,Na as Ut,O as he,Oa as jt,P as w,Pa as Gt,Q as Oe,Qa as Wt,R as ae,Ra as Ft,S as Me,T as ze,Ta as Vt,U as Y,Ua as qt,V as W,Va as Xt,W as Ct,Wa as Yt,Xa as Jt,Y as _,Ya as Qt,Z as Tt,Za as Zt,_ as Mt,_a as en,aa as g,ba as E,c as ft,ca as Z,d as s,da as z,e as f,ea as R,f as T,fa as Qe,g as ht,ga as F,h as B,ha as ge,i as Se,ia as $e,j as ue,ja as ve,ka as A,m as pe,n as D,na as U,o as Ee,oa as Nt,p as Ce,pa as Ze,qa as Dt,ra as Be,s as H,sa as M,t as Te,ta as et,u as Le,ua as _t,v as gt,va as Lt,w as y,wa as Pt,x as vt,xa as Ne,y as Q,ya as tt,z as bt}from"./chunks/chunk-JS34KXKQ.js";import{e as kt,f as xt}from"./chunks/chunk-MPNRY2JX.js";import"./chunks/chunk-VC46IEJQ.js";function be(e,t){fe(n=>t.includes(n.method)&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var st=["notes","timeline","groups","check","card","memory_show","status"];async function at(e,t){let n=e.meta??{};await H("note_add",{group:e.group,type:e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),be(e.group,st)}async function tn(e,t,n,a){await H("note_add",{group:e,type:t,description:n,body:a}),be(e,st)}async function nn(e,t){await H("memory_update",{group:e,body:t}),be(e,["memory_show","status"])}async function sn(e,t){let n=await H("proposal_show",{group:e}),a=Object.fromEntries(Object.entries(n.proposal??{}).filter(([r])=>!["schema","author","user","supersedes"].includes(r)));await H("proposal_set",{group:e,proposal:{...a,statement:t}}),be(e,["groups","proposal_show","check","summary"])}async function an(e){await H("note_rm",{note:e.id}),be(e.group,st)}async function rn(e,t,n){await H("name",{run:e,name:n}),be(t,["card","runs","groups","summary","series"])}async function Ke(e,t,n){let a=await H("view_text",{path:e,id:t,text:n});return fe(r=>["view","view_history"].includes(r.method)&&r.scope===e),a.id}async function on(e){await H("view_upgrade",{group:e}),fe(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var ye=new pe(null);async function ln(e,t){return await H("set",{key:e,value:t}),H("meta")}var V=new pe(Ee("sidebar",!0)),q=new pe(null),oe=new pe(!1),we=new pe(null);V.subscribe(e=>Ce("sidebar",e));var cn=Ee("visit",Date.now());Ce("visit",Date.now());function un(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var Ue=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var os=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function je(e){we.set(e),Pe.set(e.theme),e.settings?.theme_mode&&se.set(e.settings.theme_mode),Je()}async function rt(e,t){e==="theme_mode"&&(se.set(t),Je()),je(await ln(e,t))}function dn(){let e=D(se),t=te(),n=D(we),[a,r]=f(null);T(()=>{document.title="Settings \xB7 Beamtime"},[]);let o=(i,m)=>{r(null),rt(i,m).catch(d=>r(d.message))},l=n?.settings??{};return s`<div class="page settings">
    <header class="header"><h1 class="title" tabindex="-1">Settings</h1></header>
    <p class="muted small">Changes are written to <code>${l.file??"beamtime.yaml"}</code>, the project's settings.</p>
    ${a?s`<${z} kind="error">${a}<//>`:null}
    <h2>Appearance</h2>
    <div class="settings-rows">
      <span class="field-label">Mode</span>
      <div class="segmented" role="radiogroup" aria-label="Theme mode">
        ${os.map(([i,m,d])=>s`<button type="button" role="radio" aria-checked=${e===i} onClick=${()=>o("theme_mode",i)}>
          <${g} name=${m} size=${15} />${d}</button>`)}
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
      ${(n?.figure_styles??[]).length?s`<${Be} options=${n.figure_styles} value=${l.figure_style??[]} label="Style sheets"
            placeholder="Add a style" onChange=${i=>o("figure_style",i)} />`:s`<span class="muted small"><code>${JSON.stringify(l.figure_style??[])}</code>; choosing others needs the figures
            extra: <code>uv add matplotlib scienceplots</code></span>`}
    </div>
    <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(l.figure_style??[])})</code>, in this order
      (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
      <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <h2>Keyboard</h2>
    <table class="kv">${Ue.map(([i,m])=>s`<tr><td><kbd>${i}</kbd></td><td>${m}</td></tr>`)}</table>
    <h2>About</h2>
    <table class="kv">
      <tr><td class="muted">version</td><td>${n?.version}</td></tr>
      <tr><td class="muted">root</td><td><code>${n?.root}</code></td></tr>
      <tr><td class="muted">log dir</td><td><code>${n?.logdir}</code></td></tr>
    </table>
  </div>`}var ne=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),de=(e,t=null,n=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{}},scope:e}),ot=e=>({method:"summary",params:{path:e},scope:e}),it=e=>({method:"groups",params:{from:e,depth:0},scope:e}),mn=e=>({method:"check",params:{group:e},scope:e}),pn=e=>({method:"proposal_show",params:{group:e},scope:e}),Ge=(e,t)=>({method:"card",params:{run:Me(e,t)},scope:t}),$n=(e,t)=>({method:"output",params:{run:Me(e,t),tail:30},scope:t}),De=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),fn=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),hn=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),gn=()=>({method:"status",params:{},scope:"."}),We=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function _e(e){for(let t of[de(e),it(e),De(e),ot(e)])gt(t)}var vn=e=>({method:"view_history",params:{group:e},scope:e});var bn={system:"light",light:"dark",dark:"system"},is={system:"monitor",light:"sun",dark:"moon"};function yn(){let e=D(we),t=D(se),n=D(V);return s`<header class="topbar">
    <${U} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>V.set(!n)} />
    <a class="project" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search" onClick=${()=>q.set("")} aria-label="Search (⌘K)">
      <${g} name="search" size=${15} /><span class="search-label">Search groups, runs, commands</span><kbd>⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${ls} />
      <${U} icon=${is[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${bn[t]})`}
        onClick=${()=>{rt("theme_mode",bn[t])}} />
      <a class="icon-button" href=${Oe(W.value.page==="group"?W.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${g} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${g} name="settings" size=${16} /></a>
    </div>
  </header>`}function ls(){let t=(y(ne()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?s`${[{name:"local",state:"connected"},...t].map(n=>s`<a class=${`source ${n.state}`}
      href=${w(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${g} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:s`<span class="source" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${g} name="server" size=${15} /> local</span>`}function cs(e){let[t,n]=f(Date.now());return T(()=>{let a=setInterval(()=>n(Date.now()),e);return()=>clearInterval(a)},[e]),t}function us(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function wn(){let e=D(bt),t=D(Q),n=D(yt),a=D(W),r=cs(5e3),o=y(gn()).data,l=R(y(We()).data),i=D(we),m=o?.daemon,d=o?.runs?.running??0,u=l.filter(C=>C["run.status"]==="failed"&&us(C["run.ended_at"])>cn).length,$=o?.meta?.freshness,[p,v,x]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&m?["",`live \xB7 updated ${A(new Date(n).toISOString(),r)}`,`beamtime serve, pid ${m.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return s`<footer class="statusbar">
    <span class="status-item" data-tip=${x}><span class=${`live-dot ${p}`}></span>${v}</span>
    ${d?s`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>q.set("running")}>
          <${g} name="circle-dot" size=${14} class="tone-running" />${d} running</button>`:null}
    ${u?s`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>q.set("failed")}>
          <${g} name="circle-x" size=${14} />${u} failed since your last visit</button>`:null}
    ${$?.behind?s`<span class="status-item warn-text" data-tip=${$.text}><${g} name="hourglass" size=${14} />${$.behind} runs behind</span>`:null}
    ${$?.damaged?.length?s`<span class="status-item warn-text" data-tip=${$.damaged.join(`
`)}><${g} name="triangle-alert" size=${14} />${$.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${a.page==="group"&&a.run?s`<span class="status-item"><${g} name="activity" size=${14} />1 run selected</span>`:null}
    <${U} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>Q.set(!t)} />
    ${i?.outdated?s`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item subtle">${i?.version?`beamtime ${i.version}`:""}</span>
  </footer>`}var kn=null;function Fe(e){let t=B(null),[n,a]=f(null),[r,o]=f(!1),[l,i]=f(!1);T(()=>{let $=!0;return kn??=import("./chunks/md-FNEL5GP4.js"),kn.then(p=>p.render(e.text??"")).then(p=>$&&a(p)),()=>{$=!1}},[e.text]),ht(()=>{let $=t.current;if(!$||!e.clamp)return;let p=()=>i($.scrollHeight>$.clientHeight+2),v=new ResizeObserver(p);return v.observe($),()=>v.disconnect()},[e.clamp,n]);let m=e.clamp&&!r,d=`md${m?" clamped":""}`,u=m?`--clamp:${e.clamp}`:"";return s`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?s`<div class=${d} ref=${t} style=${u}>
          ${(e.text??"").split(/\n{2,}/).map($=>s`<p>${$}</p>`)}
        </div>`:s`<div class=${d} ref=${t} style=${u} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(l||r)?s`<button type="button" class="link more" onClick=${()=>o(!r)}>${r?"less":"more"}</button>`:null}
  </div>`}function me(e){let[t,n]=f(!!e.startEditing),[a,r]=f(e.value),[o,l]=f(null),[i,m]=f(null),d=B(null),u=B(!1);T(()=>l(null),[e.value]),T(()=>{!t||!d.current||(d.current.focus(),e.startEditing?d.current.select():d.current.setSelectionRange(d.current.value.length,d.current.value.length))},[t]);let[$,p]=f(!1),v=c=>{if(!c.target.closest("a, button, input, summary")){if(e.locked)return p(!0);c.preventDefault(),r(o??e.value),m(null),u.current=!1,n(!0)}},x=()=>{u.current=!0,n(!1),m(null),e.onCancel?.()},C=async()=>{if(u.current)return;u.current=!0;let c=e.multiline?a.trim():a.replace(/\s*\n\s*/g," ").trim();if(c===e.value.trim()||!c&&!e.multiline)return x();n(!1),l(c);try{await e.onSave(c)}catch(L){l(null),r(c),m(L.message),u.current=!1,n(!0)}},b=c=>{if(c.key==="Escape")return c.preventDefault(),c.stopPropagation(),x();c.key!=="Enter"||c.isComposing||c.keyCode===229||(!e.multiline||c.metaKey||c.ctrlKey)&&(c.preventDefault(),C())};if(t)return s`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${d} class="edit-field" value=${a} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,a.split(`
`).length+1)):1}
        onInput=${c=>r(c.target.value)} onKeyDown=${b} onBlur=${C}></textarea>
      <span class="edit-hint">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${i?s` · <span class="bad-text">${i}</span>`:null}</span>
    </div>`;let S=o??e.value;return s`<div class=${`editable${e.locked?" locked":""}${o!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${e.locked?`${e.label}: ${e.locked}`:`Edit ${e.label}`}
      data-tip=${e.locked} onClick=${v} onBlur=${()=>p(!1)}
      onKeyDown=${c=>c.key==="Enter"&&c.target===c.currentTarget&&v(c)}>
    ${S.trim()?e.render?e.render(S):S:s`<span class="subtle">${e.placeholder??"Click to write"}</span>`}
    ${$&&e.locked?s`<span class="edit-hint locked-why" role="status"><${g} name="lock" size=${12} /> ${e.locked}</span>`:null}
  </div>`}function lt(e){let t=[];if(e.effect!==void 0&&e.effect!==null){let n=e.ci?` [${F(e.ci[0])}, ${F(e.ci[1])}]`:"";t.push(`${e.effect>=0?"+":""}${F(e.effect)}${n}`)}return e.threshold!==void 0&&e.threshold!==null&&t.push(`needs ${e.op} ${F(e.threshold)}`),e.points&&t.push(`${e.points} point${e.points>1?"s":""}`),e.detail&&t.push(e.detail),t.join(" \xB7 ")}function ct(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function xn({node:e}){let t=ee("proposal"),n=ee("check"),a=t.data,r=n.data;if(!a)return s`<${Z} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let o=a.proposal??{},l=(a.versions??[]).filter(m=>m.version!==a.version),i=!e.props.of||e.props.of===".";return s`<${Z} title="Predictions" result=${t} class="proposal-block">
    ${i?null:s`<p class="statement">${o.statement}</p>`}
    ${o.rationale?s`<p class="rationale">${o.rationale}</p>`:null}
    <div class="predictions">
      ${(r?.predictions??[]).map(m=>s`<div class="prediction" key=${m.name}>
          <${E} spec=${M("result",m.result)} />
          <span class="pname">${m.name}</span>
          <span class="pdetail num">${lt(m)}</span>
        </div>`)}
    </div>
    ${l.length?s`<${Ze} summary=${`${l.length} earlier version${l.length>1?"s":""}`}>
          ${l.map(m=>s`<p class="small"><code>${m.version}</code> ${m.statement}
            <span class="muted">(${m.runs} runs, check ${m.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function Sn({node:e}){let t=ee("main"),n=e.data?.main.params.group??".",a=t.data?.chain??[],r=a.find(i=>i.group===n)??null,o=a.filter(i=>i.group!==n),l=r?.notes_since?"out of date":r?`version ${r.versions??1}`:"none yet";return s`<${Qe} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?l:void 0} open=${!1} result=${t} class="memory-block"
      action=${s`<${E} spec=${{icon:"circle-help",tone:"muted",label:ms}} />`}>
    <${me} value=${r?.body??""} label="the memory" multiline class="markdown"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${i=>s`<${Fe} text=${i} />`} onSave=${i=>nn(n,i)} />
    ${r&&(r.body?.length>(t.data?.budget??1/0)||r.notes_since>=ds)?s`<p class="memory-meta warn-text">${r.body?.length>t.data.budget?`${r.body.length} characters, beyond the budget of ${t.data.budget}`:`${r.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${r?s`<p class="memory-meta">${r.author} · covers notes until ${r.covers_until?.slice(0,10)}
          ${r.notes_since?s` · <span class="warn-text">${r.notes_since} newer note${r.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${o.length?s`<p class="memory-meta">Memory above this group: ${o.map((i,m)=>s`${m?", ":""}<a href=${w(i.group)}>${i.group==="."?"local":i.group}</a>`)}</p>`:null}
  <//>`}var ds=5,ms="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",ps="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function En({node:e}){let t=ee("main"),n=e.data?.main.params.from??".",a=R(t.data).filter(r=>r.path!==n);return s`<${Z} title=${e.props.title} count=${t.data?String(a.length):void 0} result=${t}>
    ${t.data&&!a.length?s`<${z}>No groups below.<//>`:null}
    <div class="group-list">
      ${a.map(r=>{let[o,l]=ct(r.progress),i=(r.failed??0)+(r.killed??0)+(r.lost??0);return s`<a class="group-row" key=${r.path} href=${w(r.path)}
            onPointerEnter=${()=>_e(r.path)} onFocus=${()=>_e(r.path)}>
          <${E} spec=${M("research",r.status)} />
          <span class="gname">${r.path.split("/").pop()}</span>
          <span class="gfacts">
            ${r.check?s`<${E} spec=${M("result",r.check)} word />`:null}
            ${r.verdict?s`<${E} spec=${M("verdict",r.verdict)} />`:null}
            ${o?s`<span data-tip=${l}>${o}</span>`:null}
            <span class="num"><b>${r.runs}</b> runs</span>
            ${r.running?s`<${E} spec=${M("run","running")} />`:null}
            ${i?s`<span class="tone-bad num" data-tip="failed, killed or lost"><${g} name="circle-x" size=${14} /> ${i}</span>`:null}
          </span>
          ${r.proposal?s`<span class="gstatement">${r.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function Cn({node:e}){let t=ee("main"),n=e.data?.main.params.from??".",[a,r]=f(!1),o=(t.data?.entries??[]).filter(i=>!String(i.state??"").startsWith("superseded")),l=t.data?.meta?.matched??o.length;return s`<${Qe} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(l):void 0} result=${t}
      action=${s`<${E} spec=${{icon:"circle-help",tone:"muted",label:ps}} />
        <${U} icon="plus" label="Add a note" onClick=${()=>r(!0)} />`}>
    <div class="notes">
      ${a?s`<${hs} group=${n} onDone=${()=>r(!1)} />`:null}
      ${t.data&&!o.length&&!a?s`<p class="muted small">No notes yet.</p>`:null}
      ${o.map(i=>s`<${Ve} key=${i.id} note=${i} scope=${n} />`)}
      ${t.data?.more&&e.data?s`<${Tn} call=${e.data.main} before=${o[o.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var $s=20;function Tn(e){let[t,n]=f(!1),a=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:$s}}:null,r=y(a);if(!t)return s`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(r.status==="error")return s`<p class="bad-text small">${r.error}</p>`;let o=r.data?.entries??[];return s`${r.data?null:s`<div class="skeleton" style="block-size: 40px"></div>`}
    ${o.map(l=>s`<${Ve} key=${l.id} note=${l} scope=${e.scope} />`)}
    ${r.data?.more?s`<${Tn} call=${e.call} before=${o[o.length-1]?.id} scope=${e.scope} />`:null}`}var fs=["observation","idea","question","decision"];function hs(e){let[t,n]=f("observation"),[a,r]=f(""),[o,l]=f(""),[i,m]=f(null),[d,u]=f(!1),$=async v=>{if(v.preventDefault(),!a.trim())return m("give the note a title");u(!0);try{await tn(e.group,t,a.trim(),o.trim()),e.onDone()}catch(x){m(x.message),u(!1)}};return s`<form class="note new-note" onSubmit=${$} onKeyDown=${v=>{v.key==="Escape"&&e.onDone(),v.key==="Enter"&&(v.metaKey||v.ctrlKey)&&$(v)}}>
    <div class="note-line">
      <select class="note-type" value=${t} aria-label="Note type" onChange=${v=>n(v.target.value)}>
        ${fs.map(v=>s`<option value=${v}>${v}</option>`)}
      </select>
      <input class="new-note-title" value=${a} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${v=>r(v.target.value)} />
    </div>
    <textarea class="new-note-body" rows="4" value=${o} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${v=>l(v.target.value)}></textarea>
    <div class="save-actions">
      <button type="submit" class="button primary" disabled=${d}>${d?"Adding\u2026":"Add note"}</button>
      <button type="button" class="link small" onClick=${e.onDone}>cancel</button>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${i?s`<span class="bad-text small">${i}</span>`:null}
    </div>
  </form>`}function Ve(e){let t=e.note,[n,a]=f(!!e.open),[r,o]=f(!1),l=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,i=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),m=t.meta?.author;return s`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${d=>!d.target.closest(".editable, a, .note-delete")&&a(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${g} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${E} spec=${M("note",t.type)} />
      <${me} value=${t.description} label="the note's title" class="note-title" render=${vs}
        onSave=${d=>at(t,{description:d})} />
      ${t.overall?s`<${E} spec=${M("verdict",t.overall)} />`:null}
      ${t.state?s`<span class="tag tone-warn">${t.state}</span>`:null}
      ${l?s`<a class="note-group" href=${w(l)} data-tip="from this group">${gs(l,e.scope)}</a>`:null}
      <span class="note-meta">${m?`${m} \xB7 `:""}${A(i)}</span>
      <${U} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${r}
        onClick=${d=>{d.stopPropagation(),o(!r)}} />
    </div>
    ${r?s`<div class="note-confirm" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <button type="button" class="button danger" onClick=${()=>{an(t)}}>Delete</button>
          <button type="button" class="link small" onClick=${()=>o(!1)}>cancel</button>
        </div>`:null}
    ${n?s`<${me} value=${t.body??""} label="the note" multiline class="note-body markdown"
          placeholder="Add details in Markdown" render=${d=>s`<${Fe} text=${d} />`}
          onSave=${d=>at(t,{body:d})} />`:null}
  </article>`}function gs(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,a=n.split("/").pop()??n;return he(a)?a.slice(-8):n}function Mn({node:e}){let t=ee("main"),n=t.data?.lines??[],a=t.data?.meta??{},r=s`<${g} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${a.total_lines??n.length} lines${(a.shown??0)<(a.total_lines??0)?`, last ${a.shown}`:""}`:""}</span>`;return s`<${Z} result=${t}>
    <${Ze} summary=${r} open=${e.props.open}>
      <pre class="log">${n.join(`
`)}</pre>
    <//>
  <//>`}function Nn({node:e}){let t=ue(X);return s`<${Z} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${me} value=${e.props.text??""} label="the text" multiline class="markdown"
      startEditing=${ye.value===e.id} onCancel=${()=>ye.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>s`<${Fe} text=${n} />`}
      onSave=${n=>(ye.set(null),Ke(t.path,e.id,n))} />
  <//>`}function Dn({node:e}){return s`<${z} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function vs(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let a=n.slice(2,-2),[r]=a.split(/[#@]/),o=r.split("/").pop()??"";return s`<a href=${he(o)?ae(o):w(r)}>${a}</a>`}return n.startsWith("`")?s`<code>${n.slice(1,-1)}</code>`:n})}function _n(e){let t=()=>_(w(e.path),{replace:!0});return s`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head">
      <span class="status-item"><${g} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${U} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?s`<${bs} id=${e.run} scope=${e.path} />`:s`<${ys} path=${e.path} />`}
  </aside>`}function bs({id:e,scope:t}){let n=y(Ge(e,t)).data,a=y($n(e,t)).data,r=y(De(t)).data,o=te(),l=Se(()=>Ie(R(r).map(d=>d["run.id"]),o).get(e),[r,o,e]);if(!n)return s`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let i=n.run,m=Object.entries(n.metrics??{});return s`<div class="drawer-body">
    <h3><span class="run-dot" style=${`background:${l??"var(--bt-subtle)"}`}></span>
      <a href=${ae(e)}>${i.name}</a></h3>
    <p class="facts small">
      <${E} spec=${M("run",i.status)} word />
      <span class="fact"><b>${$e(i.steps)}</b> steps</span>
      <span class="fact"><b>${ve(i.duration_s)}</b></span>
      <span class="fact" data-tip=${i.created_at}>${A(i.created_at)}</span>
    </p>
    ${i.error?s`<pre class="log bad-text">${i.error}</pre>`:null}
    <h4>Config</h4>
    <table class="kv">${Object.entries(n.config??{}).map(([d,u])=>s`<tr><td>${d}</td><td class="num">${F(u)}</td></tr>`)}</table>
    ${m.length?s`<h4>Metrics</h4>
          <table class="kv">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${m.map(([d,u])=>s`<tr><td>${d}</td><td class="num"><b>${F(u.last)}</b></td>
              <td class="num">${F(u.min)}</td><td class="num">${F(u.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?s`<h4>Cited by</h4>${n.cited_by.map(d=>s`<p class="small"><${E} spec=${M("note",d.type)} /> ${d.description}</p>`)}`:null}
    <h4>Events</h4>
    ${(n.events??[]).slice(-8).map(d=>s`<div class="event"><span class="muted num">${d.t?.slice(5,16).replace("T"," ")}</span>
        <${g} name=${et(d.type)} size=${14} /><span>${d.description}</span></div>`)}
    <h4>Output</h4>
    <pre class="log">${(a?.lines??[]).join(`
`)}</pre>
  </div>`}function ys({path:e}){let t=y(fn(e)).data,n=y(hn(e)).data;return s`<div class="drawer-body">
    <h4 style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?s`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(a=>!String(a.state??"").startsWith("superseded")).map(a=>s`<${Ve} key=${a.id} note=${a} />`)}</div>
    <h4>Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(a=>s`<div class="event"><span class="muted num">${a.t?.slice(5,16).replace("T"," ")}</span>
        <${g} name=${a.kind==="note"?"file-text":et(a.type)} size=${14} />
        <span>${a.run?s`<a href=${ae(a.run)}>${a.run.slice(-8)}</a> `:null}${a.description??a.type}</span></div>`)}
  </div>`}var ut=["failed","killed","lost"];function dt(e){let t=ze(e.path),n=t==="."?e.path:e.path.slice(t.length+1),a=Y(e.path)?[]:n.split("/"),r=a.length&&he(a[a.length-1])?a[a.length-1]:null,o=a.slice(0,-1),l=i=>[...t==="."?[]:[t],...o.slice(0,i+1)].join("/");return s`<header class="header">
    <nav class="crumbs" aria-label="Breadcrumb">
      ${a.length?s`<a href=${w(t)}>${t==="."?"local":t}</a>`:null}
      ${o.map((i,m)=>s`<span class="sep">/</span><a href=${w(l(m))}>${i}</a>`)}
    </nav>
    ${r?s`<${ks} id=${r} scope=${e.path} />`:s`<${ws} path=${e.path} />`}
    ${e.finding?s`<p class="finding">${e.finding}</p>`:null}
  </header>`}function ws({path:e}){let t=R(y(it(e)).data)[0]??null,n=y(t?.proposal?mn(e):null).data,a=y(t?.proposal?pn(e):null).data,r=a?.proposal?.rationale,o=a?.versions?.find(u=>u.version===a.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,l=e==="."?"local":e.split("/").pop();if(!t)return s`<h1 class="title" tabindex="-1">${l}</h1><div class="skeleton late" style="block-size: 52px"></div>`;let[i,m]=ct(n?.progress?.text??t.progress),d=ut.reduce((u,$)=>u+(t[$]??0),0);return s`
    <h1 class="title" tabindex="-1">${l} <${E} spec=${M("research",t.status)} word /></h1>
    ${t.proposal?s`<div class="statement">
          <${me} value=${t.proposal} label="the proposal's statement" locked=${a?o:"Loading the proposal\u2026"}
            render=${u=>s`<span data-tip=${o?void 0:r}>${u}</span>`}
            onSave=${u=>sn(e,u)} />
        </div>`:null}
    ${t.proposal?s`<div class="preds">
          ${(n?.predictions??[]).map(u=>s`<span class="pred" key=${u.name} data-tip=${lt(u)}>
              <${E} spec=${M("result",u.result)} /><b>${u.name}</b></span>`)}
          ${n?.provisional?s`<span class="tag tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
          ${i?s`<span class="pred"><${Nt} fraction=${n?.progress?.fraction??null} label=${m??i} />
                <span data-tip=${m}>${i}</span></span>`:null}
          ${t.verdict?s`<span class="pred"><${E} spec=${M("verdict",t.verdict)} word /></span>`:null}
        </div>`:null}
    <div class="facts">
      <span class="fact"><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?s`<span class="fact"><${E} spec=${M("run","running")} /><b>${t.running}</b> running</span>`:null}
      ${t.finished?s`<span class="fact"><${E} spec=${M("run","finished")} /><b>${t.finished}</b> finished</span>`:null}
      ${d?s`<span class="fact tone-bad" data-tip=${ut.filter(u=>t[u]).map(u=>`${t[u]} ${u}`).join(", ")}>
            <${g} name="circle-x" size=${15} /><b class="tone-bad">${d}</b> ${d===1?ut.find(u=>t[u]):"ended early"}</span>`:null}
      ${t.notes?s`<span class="fact"><${g} name="file-text" size=${15} /><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${Ln} path=${e} />
    </div>`}function ks({id:e,scope:t}){let n=y(Ge(e,t)).data;if(!n)return s`<h1 class="title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 52px"></div>`;let a=n.run,r=()=>{navigator.clipboard?.writeText(a.id)};return s`
    <h1 class="title" tabindex="-1"><${me} value=${a.name??a.id} label="the run's name" class="title-edit"
        onSave=${o=>rn(a.id,t,o.trim())} />
      <${E} spec=${M("run",a.status)} word /></h1>
    ${a.error?s`<p class="statement bad-text" data-tip=${a.error}>${a.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span class="fact"><b>${$e(a.steps)}</b> steps</span>
      <span class="fact"><b>${ve(a.duration_s)}</b></span>
      <span class="fact" data-tip=${a.created_at}>${A(a.created_at)}</span>
      <${Ln} path=${t} />
      <span class="fact">
        <${U} icon="copy" label=${`Copy the run id ${a.id}`} onClick=${r} />
        <${Dt} icon="ellipsis" label="Details" title="Run details" class="run-details">
          <table class="kv">${xs(a).map(([o,l])=>s`<tr><td class="muted">${o}</td><td>${l}</td></tr>`)}</table>
          <div class="menu-list">
            <button type="button" onClick=${()=>_(w(t,{run:a.id}),{replace:!0})}>
              <${g} name="panel-right" size=${15} /> Open in the side panel</button>
            <button type="button" onClick=${r}><${g} name="copy" size=${15} /> Copy the run id</button>
            ${a.git?.commit?s`<button type="button" onClick=${()=>navigator.clipboard?.writeText(a.git.commit)}>
              <${g} name="git-commit" size=${15} /> Copy the commit</button>`:null}
          </div>
        <//>
      </span>
    </div>
    ${(n.proposals??[]).length?s`<div class="preds" style="margin-block-start: 10px">
          ${n.proposals.map(o=>s`<a class="pred" href=${w(o.group)} data-tip=${o.statement}>
              <${E} spec=${M("result",o.check)} /><b>${o.group==="."?"own proposal":o.group}</b>
              ${o.verdict?s`<${E} spec=${M("verdict",o.verdict)} />`:null}</a>`)}
        </div>`:null}`}function Ln({path:e}){let t=y(ot(e)).data?.summary;if(!t)return null;let n=Object.entries(t.config??{}).map(([r,o])=>`${r} ${F(o)}`).join(", "),a=he(e.split("/").pop()??"");return s`<span class="fact" data-tip=${`${t.stat} of ${t.metric} over ${a?"the run":"all runs"}`}>
    best <b>${t.metric} ${F(t.value)}</b>
    ${a?null:s`<span>· <a href=${ae(t.run)}>${t.name}</a>${n?s` <em>(${n})</em>`:null}</span>`}
  </span>`}function xs(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,a])=>[n,String(a)])}var Pn=15e3;function Rn({node:e}){let t=ue(X),n=te(),[a,r]=Et(),o=e.props.code,l=y(r&&o?{method:"code",params:o,scope:t.path}:null),[i,m]=f(null),[d,u]=f(120),[$,p]=f({error:null,warnings:[]}),v=b=>{re&&console.error(`[block ${e.id}] ${b}`),p(S=>({...S,error:b}))};T(()=>{let b=i?.contentWindow;if(!b||l.status!=="ready")return;let S=O=>b.postMessage(O,"*"),c=new Map,L=new Kt,h=!0;Te.n++;let I=()=>{h&&Te.n--,h=!1},j=setTimeout(()=>{h&&v(`no first render within ${Pn/1e3} s`),I()},Pn),K=O=>{if(O.source!==b)return;let k=O.data;switch(k.type){case"hello":S({type:"init",init:{id:e.id,code:l.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:St.value,pair:Pe.value,prefs:nt(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics}});break;case"sub":if(!Bt.has(k.call.method)){S({type:"result",id:k.id,result:{status:"error",data:null,error:`${k.call.method} is not available in a custom block`,refreshing:!1}});break}c.get(k.id)?.(),c.set(k.id,vt(k.call,xe=>S({type:"result",id:k.id,result:xe})));break;case"unsub":c.get(k.id)?.(),c.delete(k.id);break;case"navigate":k.url.startsWith("/")&&_(k.url);break;case"height":L.accept(performance.now())?u(Math.max(40,k.height)):P("its height keeps changing, so it is fixed at its last height");break;case"ready":p(xe=>({...xe,blank:k.blank,overflow:k.overflow})),I();break;case"warn":P(k.message);break;case"hover":Ye.set(k.run);break;case"prefs":JSON.stringify(N.value)!==JSON.stringify(k.prefs)&&N.set(k.prefs);break;case"download":case"snapshot":k.href?Ht(k.href,k.name)?performance.now()-G>1e3&&(G=performance.now(),Lt(k.href,k.name)):P(`a download of ${k.name} was refused: only PNG, SVG and CSV files`):P("it draws no SVG or canvas to download");break;case"figure":Pt(k.spec,k.name).catch(xe=>P(`the PDF failed: ${xe.message}`));break;case"expand":At(k.node)&&tt().expand(k.node,t);break;case"error":v(k.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,x)),I();break;default:break}},P=O=>{re&&console.warn(`[block ${e.id}] ${O}`),p(k=>k.warnings.includes(O)?k:{...k,warnings:[...k.warnings,O]})},G=0,N=nt(t.path),J=Ye.subscribe(O=>S({type:"hover",run:O})),ce=N.subscribe(O=>S({type:"prefs",prefs:O}));return addEventListener("message",K),S({type:"ping"}),()=>{J(),ce(),removeEventListener("message",K),clearTimeout(j);for(let O of c.values())O();I()}},[l.status,l.data,i]),T(()=>{let b={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};i?.contentWindow?.postMessage(b,"*")},[t.names,t.colors,t.metrics,i]),T(()=>{n&&i?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let x=typeof o=="object"?o.path??o.block:String(o??""),C=r&&l.status==="ready"&&!$.error;return s`<div ref=${a} class="custom-block">
    <div class="chart-head">
      <span class="chart-title">${e.props.title??""}</span>
      ${C?s`<span class="chart-tools">
            <${U} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?s`<${U} icon="x" label="Close (Esc)" onClick=${()=>Ne.set(null)} />`:s`<${U} icon="maximize" label="Expand" onClick=${()=>tt().expand(e,t)} />`}
          </span>`:null}
    </div>
    <${Z} caption=${e.props.expanded?void 0:e.props.caption} result=${l}>
      ${$.error?s`<div class="notice error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${x})</span>
            <pre>${$.error}</pre>
          </div>`:null}
      ${$.warnings.map(b=>s`<${z} kind="warning">${b}<//>`)}
      ${C?s`<div class="custom-frame" data-frame-blank=${$.blank?"1":void 0} data-frame-overflow=${$.overflow?"1":void 0}>
            <iframe key=${l.data.code} ref=${m} src="/static/kit/frame.html" sandbox="allow-scripts" title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${d}px`} />
          </div>`:null}
    <//>
  </div>`}function In({node:e}){let t=ee("main"),n=ue(X),a=t.data?.entries??[];return s`<${Z} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!a.length?s`<${z}>No images logged.<//>`:null}
    <div class="images">
      ${a.map(r=>s`<figure key=${`${r.run}/${r.path}`}>
          <img src=${`/api/file/${Me(r.run,n.path)}/${r.path}`} alt=${r.caption??e.props.title} loading="lazy" />
          <figcaption>step ${$e(r.step)}${r.caption?` \xB7 ${r.caption}`:""}</figcaption>
        </figure>`)}
    </div>
  <//>`}function On({node:e}){let t=ee("main"),n=t.data?.entries??[];return s`<${Z} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?s`<${z}>No text logged.<//>`:null}
    ${n.map(a=>s`<div class="text-entry" key=${`${a.run}/${a.step}`}>
        <div class="muted small">step ${$e(a.step)}${a.caption?` \xB7 ${a.caption}`:""}</div>
        <pre>${a.text??""}</pre>
      </div>`)}
  <//>`}function zn({node:e}){let[t,n]=f(e.props.open!==!1),a=s`${(e.children??[]).map(r=>s`<${le} key=${r.id} node=${r} />`)}`;return e.props.title?s`<section class="section">
    <button type="button" class="section-title" aria-expanded=${t} onClick=${()=>n(!t)}>
      <${g} name=${t?"chevron-down":"chevron-right"} size=${16} />${e.props.title}
    </button>
    ${t?s`<div class="stack">${a}</div>`:null}
  </section>`:s`<div class="stack">${a}</div>`}function Bn({node:e}){return s`<div class="row">
    ${(e.children??[]).map(t=>s`<${le} key=${t.id} node=${t} />`)}
  </div>`}function Hn({node:e}){let t=ue(X),n=He(t.path),a=e.props.min_width??320,r=e.props.columns,o=r?`grid-template-columns: repeat(${r}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${a}px, 100%), 1fr))`,l=(e.children??[]).flatMap(u=>u.props.y??[]),i=e.props.addable?n.added.filter(u=>!l.includes(u)).map(u=>({block:"line",id:`added-${u}`,props:{y:u,added:!0},data:{main:{...e.props.template,params:{...e.props.template.params,y:[u]}}}})):[],m=zt([...e.children??[],...i],n.order[e.id]),d=(u,$)=>{let p=m.map(v=>v.id).filter(v=>v!==u);p.splice(p.indexOf($),0,u),It(t.path,e.id,p)};return s`<div class="grid" style=${o}>
    ${m.map(u=>s`<${Ss} key=${u.id} node=${u} path=${t.path} span=${n.spans[u.id]??u.props.span??1}
      columns=${r} onDrop=${$=>$!==u.id&&d($,u.id)} />`)}
    ${e.props.addable?s`<${Es} path=${t.path} shown=${[...l,...n.added]} />`:null}
  </div>`}var mt=[1,2,"full"];function Ss(e){let[t,n]=f(!1),a=mt[(mt.indexOf(e.span)+1)%mt.length],r=o=>o==="full"?"full width":`${o} column${o===1?"":"s"}`;return s`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${o=>{o.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${o=>{o.preventDefault(),n(!1),e.onDrop(o.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${o=>o.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${g} name="grip" size=${14} /></span>
      <button type="button" class="cell-width" data-tip=${`Width: ${r(e.span)}; click for ${r(a)}`}
        aria-label=${`Width ${r(e.span)}`} onClick=${()=>Ot(e.path,e.node.id,a)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${le} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function Es(e){let t=y({method:"keys",params:{from:e.path},scope:e.path}).data,n=(t?.metrics?.rows??[]).map(a=>a[0]).filter(a=>!e.shown.includes(a));return t&&!n.length?null:s`<div class="add-chart">
    <span class="add-chart-label"><${g} name="plus" size=${16} /> Add a chart</span>
    <${Be} single options=${n} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
      onChange=${([a])=>Ae(e.path,r=>({added:[...r.added,a]}))} />
  </div>`}function An({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[a,r]=f(()=>t.find(i=>i.id===n())?.id??t[0]?.id),o=i=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(i)}`),r(i)},l=t.find(i=>i.id===a)??t[0];return s`<div class="tabs">
    <div class="tab-list" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(i=>s`<button type="button" role="tab" id=${`tab-${i.id}`} aria-selected=${i.id===l?.id}
          aria-controls=${`panel-${i.id}`} onClick=${()=>o(i.id)}>${i.props.title??i.id}</button>`)}
    </div>
    ${l?s`<div class="stack" role="tabpanel" id=${`panel-${l.id}`} aria-labelledby=${`tab-${l.id}`}>
          ${(l.children??[]).map(i=>s`<${le} key=${i.id} node=${i} />`)}
        </div>`:null}
  </div>`}var Cs={section:zn,row:Bn,grid:Hn,line:qt,table:Zt,stat:Qt,images:In,text:On,proposal:xn,note:Dn,output:Mn,memory:Sn,groups:En,notes:Cn,tabs:An,scatter:Xt,bar:Yt,histogram:Jt,data_table:Gt,timeline:Wt,custom:Rn,markdown:Nn};function le({node:e}){return s`<${_t} node=${e} blocks=${Cs} />`}function Kn(e,t){let n=e.split(`
`),a=t.split(`
`),r=n.length,o=a.length,l=Array.from({length:r+1},()=>new Uint32Array(o+1));for(let u=r-1;u>=0;u--)for(let $=o-1;$>=0;$--)l[u][$]=n[u]===a[$]?l[u+1][$+1]+1:Math.max(l[u+1][$],l[u][$+1]);let i=[],m=0,d=0;for(;m<r&&d<o;)n[m]===a[d]?(i.push({kind:"same",text:n[m]}),m++,d++):l[m+1][d]>=l[m][d+1]?i.push({kind:"removed",text:n[m++]}):i.push({kind:"added",text:a[d++]});for(;m<r;)i.push({kind:"removed",text:n[m++]});for(;d<o;)i.push({kind:"added",text:a[d++]});return i}function Un(e,t=3){let n=[],a=0;for(;a<e.length;){if(e[a].kind!=="same"){n.push(e[a++]);continue}let r=a;for(;r<e.length&&e[r].kind==="same";)r++;let o=a===0?0:t,l=r===e.length?0:t;r-a>o+l+1?n.push(...e.slice(a,a+o),{kind:"skip",count:r-a-o-l},...e.slice(r-l,r)):n.push(...e.slice(a,r)),a=r}return n}function qe(e){let t=y(De(e.path)),n=te(),a=R(t.data),r=Se(()=>Ie(a.map(i=>i["run.id"]),n),[t.data,n]),o=Se(()=>new Map(a.map(i=>[i["run.id"],i["run.name"]??i["run.id"]])),[t.data]);if(!e.view)return s`<div class="view"><div class="skeleton late" style="block-size: 320px"></div></div>`;let l={path:e.path,colors:r,names:o,metrics:e.view.metrics??{}};return s`<div class="view"><${X.Provider} value=${l}><${le} node=${e.view.view} /><//></div>`}function jn(e){let t=e.view,n=D(W),a=n.page==="group"&&n.version,r=t.versions?s`<a href=${w(e.path,{history:!0})}><${g} name="history" size=${14} /> history (${t.versions})</a>`:null,o;switch(t.source){case"draft":o=s`draft <b>${t.draft}</b>`;break;case"view":o=s`${t.title?s`<em>${t.title}</em> · `:null}saved ${A(ge(t.version))} by ${t.author??"unknown"}`;break;default:o=s`the built-in view`}return s`<div class="view-source">
    <${g} name="layout" size=${14} /><span>${o}</span>
    ${a?s`<a href=${w(e.path)}>an older version · show the current one</a>`:null}
    ${r}
    ${t.outdated?.length&&!a?s`<${Ts} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||a?null:s`<${Ms} path=${e.path} />
        <${Ns} path=${e.path} view=${t} />`}
  </div>`}function Ts(e){let[t,n]=f(null),a=e.outdated.map(o=>o.name).join(", ");return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{await on(e.path)}catch(o){n(o.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${a} exists; update re-pins this view to it (a new version)`}>
      <${g} name="update" size=${14} /> update ${a}</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function Ms(e){let[t,n]=f(null);return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{ye.set(await Ke(e.path,null,""))}catch(r){n(r.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${g} name="file-text" size=${14} /> add text</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function Ns(e){let t=He(e.path),n=Rt(t),[a,r]=f(!1),[o,l]=f(e.view.title??""),[i,m]=f(e.view.finding??""),[d,u]=f(null),[$,p]=f(!1);if(!n&&!a)return null;let v=async x=>{x.preventDefault(),p(!0),u(null);try{let C={charts:t.charts,added:t.added,order:t.order,spans:t.spans};await H("save_view",{path:e.path,prefs:C,title:o,finding:i}),Ae(e.path,()=>({view:{},charts:{},added:[],order:{},spans:{}})),fe(b=>["view","view_history","summary"].includes(b.method)&&b.scope===e.path),r(!1)}catch(C){u(C.message)}finally{p(!1)}};return a?s`<form class="save-form" onSubmit=${v}>
    <label class="field"><span class="field-label">Title</span>
      <input value=${o} onInput=${x=>l(x.target.value)} /></label>
    <label class="field"><span class="field-label">Finding</span>
      <input value=${i} placeholder="the key result in one sentence"
        onInput=${x=>m(x.target.value)} /></label>
    <div class="save-actions">
      <button type="submit" class="button primary" disabled=${$}>${$?"Saving\u2026":"Save as view"}</button>
      <button type="button" class="link small" onClick=${()=>r(!1)}>cancel</button>
      ${d?s`<span class="bad-text small">${d}</span>`:null}
    </div>
  </form>`:s`<button type="button" class="link small save-view" onClick=${()=>r(!0)}
        data-tip="Save your chart settings and added charts as this page's view, for everyone">
      <${g} name="save" size=${14} /> Save as view</button>`}function Gn(e){let t=y(vn(e.path)),n=t.data?.entries??[],[a,r]=f(null),o=a??n.slice(0,2).map(i=>i.version).reverse(),l=i=>{let m=o.includes(i)?o.filter(d=>d!==i):[...o,i].slice(-2);r(m.sort())};return t.status==="error"?s`<${z} kind="error">${t.error}<//>`:s`<section class="history">
    <h2 class="history-title"><${g} name="history" size=${18} /> View history</h2>
    ${t.data&&!n.length?s`<${z}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((i,m)=>s`<li key=${i.version} class=${o.includes(i.version)?"picked":""}>
          <label><input type="checkbox" checked=${o.includes(i.version)} onChange=${()=>l(i.version)} />
            <span class="num muted" data-tip=${i.version}>${A(i.time)}</span>
            <b>${i.title??"untitled"}</b><span class="muted">${i.author??""}</span>
            ${i.message?s`<span>${i.message}</span>`:null}</label>
          <a href=${m===0?w(e.path):w(e.path,{version:i.version})}
            onClick=${d=>{d.preventDefault(),_(m===0?w(e.path):w(e.path,{version:i.version}))}}>${m===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${o.length===2?s`<${Ds} path=${e.path} a=${o[0]} b=${o[1]} />`:null}
  </section>`}function Ds(e){let t=i=>({method:"view_show",params:{group:e.path,version:i},scope:e.path}),n=y(t(e.a)).data,a=y(t(e.b)).data,r=y(de(e.path,e.a)).data,o=y(de(e.path,e.b)).data,l=n&&a?Un(Kn(n.yaml,a.yaml)):[];return s`<div class="compare">
    <h3 class="block-title">Changes from ${A(ge(e.a))} to ${A(ge(e.b))}</h3>
    <pre class="diff">${l.map(i=>i.kind==="skip"?s`<div class="diff-skip">⋯ ${i.count} unchanged lines</div>`:s`<div class=${`diff-${i.kind}`}>${i.kind==="added"?"+ ":i.kind==="removed"?"\u2212 ":"  "}${i.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title">${r?.title??e.a}</h3><${qe} path=${e.path} view=${r} /></div>
      <div><h3 class="block-title">${o?.title??e.b}</h3><${qe} path=${e.path} view=${o} /></div>
    </div>
  </div>`}function Wn(e){return T(()=>{document.title=`${e.path==="."?"local":e.path} \xB7 Beamtime`},[e.path]),e.history?s`<div class="page"><${dt} path=${e.path} /><${Gn} path=${e.path} /></div>`:s`<div class="page">
    <${_s} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function _s(e){let t=y(de(e.path,e.version,e.draft));return T(()=>{t.status==="ready"&&requestAnimationFrame(Tt)},[t.status==="ready"]),s`
    <${dt} path=${e.path} finding=${t.data?.finding} />
    ${t.data?s`<${jn} path=${e.path} view=${t.data} />`:null}
    ${t.status==="error"?Ls(e.path,t.error)?s`<${z} kind="warning">${t.error} The page fills in once the remote answers again.<//>`:s`<${z} kind="error">${t.error}<//>`:s`<${qe} path=${e.path} view=${t.data} />`}`}function Ls(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function Fn(e){T(()=>{Le(de(e.id)).then(n=>_(w(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=y(de(e.id));return t.status==="error"?s`<div class="page"><${z} kind="error">${t.error}<//></div>`:s`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var pt=20,ke=-1,Ps=[["day",86400],["week",7*86400],["month",30*86400]];function qn(e){let t=R(y(ne()).data).map(i=>i.path),n=y({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),a=y({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});T(()=>{document.title="Timeline \xB7 Beamtime"},[]);let r=Date.now()/1e3,o=R(n.data).filter(i=>i["run.created_at"]).map((i,m)=>({id:i["run.id"],name:i["run.name"]??i["run.id"],group:i["run.group"],status:i["run.status"],start:Date.parse(i["run.created_at"])/1e3,end:i["run.ended_at"]?Date.parse(i["run.ended_at"])/1e3:r,lane:m})),l=(a.data?.entries??[]).map(i=>({id:i.id,type:i.type,group:i.group,description:i.description,t:Date.parse(ge(i.id))/1e3}));return s`<div class="page timeline-page">
    <header class="header">
      <h1 class="title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <label class="field inline"><span class="field-label">Group</span>
          <select value=${e.from} onChange=${i=>_(Oe(i.target.value),{replace:!0})}>
            ${t.map(i=>s`<option value=${i}>${i==="."?"everything":i}</option>`)}
          </select></label>
        <span class="muted small">${o.length} runs · ${l.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header>
    ${n.status==="error"?s`<p class="notice error">${n.error}</p>`:null}
    ${n.data&&a.data?s`<${Rs} bars=${o} marks=${l} />`:s`<div class="skeleton late" style="block-size: 320px"></div>`}
  </div>`}function Rs(e){let t=te(),n=B(null),a=[...e.bars.flatMap(b=>[b.start,b.end]),...e.marks.map(b=>b.t)],r=a.length?Vn(Math.min(...a),Math.max(...a)):Vn(Date.now()/1e3-86400,Date.now()/1e3),[o,l]=f(r),i=e.bars.length,m=Math.min(900,Math.max(160,(i+1.5)*pt+40)),u=Ft(n,Vt,t?(b=>{let S=Ut(o[0],o[1]),c=h=>String(b.colors[h]??b.colors.muted),L=h=>String(b.colors[h==="verdict"?"good":h==="decision"?"accent":h==="question"?"warn":"muted"]);return{style:xt(b),height:m,x:{range:o,log:!1,format:h=>jt(h,S.step),splits:S.at},y:{range:[ke-.8,i+.5],log:!1,reverse:!0,size:150,splits:i<=40?[ke,...e.bars.map(h=>h.lane)]:[ke],format:h=>h===ke?"notes":Hs(e.bars[Math.round(h)]?.name??"")},draw:({ctx:h,x:I,y:j,px:K,focused:P})=>{let G=pt*.62*K;for(let N of e.bars){let J=I(N.start),ce=Math.max(3*K,I(N.end)-J);h.fillStyle=P!==null&&P!==N.id?kt(c(N.status),.35):c(N.status),h.beginPath(),h.roundRect(J,j(N.lane)-G/2,ce,G,3*K),h.fill()}for(let N of e.marks){let J=I(N.t),ce=j(ke),O=(P===N.id?6:4.5)*K;h.fillStyle=L(N.type),h.beginPath(),h.moveTo(J,ce-O),h.lineTo(J+O,ce),h.lineTo(J,ce+O),h.lineTo(J-O,ce),h.closePath(),h.fill()}},hit:(h,I,j,K)=>{if(Math.abs(I-K(ke))<pt/2){let N=Bs(e.marks,J=>Math.abs(j(J.t)-h),8);return N?{key:N.id,rows:Os(N)}:null}let P=Math.round((I-K(0))/(K(1)-K(0))),G=e.bars.find(N=>N.lane===P&&j(N.start)-3<=h&&h<=Math.max(j(N.end),j(N.start)+3)+3);return G?{key:G.id,rows:Is(G)}:null},onClick:h=>{let I=e.marks.find(j=>j.id===h);I?_(w(I.group,{drawer:!0})):_(ae(h))}}})(t):null,[o,e.bars,e.marks],t),$=b=>{if(!u.current)return;b.preventDefault();let S=u.current.xAt(b.clientX),c=Math.exp(b.deltaY*.0015);l(([L,h])=>$t([S-(S-L)*c,S+(h-S)*c],r))},p=B(null),v=b=>p.current={x:b.clientX,range:o},x=b=>{if(!p.current||!u.current||!(b.buttons&1))return;let S=(b.clientX-p.current.x)*u.current.xPerPixel(),[c,L]=p.current.range;Math.abs(b.clientX-p.current.x)>3&&l($t([c-S,L-S],r))},C=Math.max(...a,Date.now()/1e3);return s`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${Ps.map(([b,S])=>s`<button type="button" role="radio" aria-checked=${Math.abs(o[1]-o[0]-S)<1}
          onClick=${()=>l($t([C-S,C+S*.02],[Math.min(r[0],C-S),r[1]]))}>last ${b}</button>`)}
      <button type="button" role="radio" aria-checked=${o[0]===r[0]&&o[1]===r[1]} onClick=${()=>l(r)}>all</button>
    </div>
    <div class="chart" ref=${n} style=${`min-block-size:${m}px`}
      onWheel=${$} onPointerDown=${v} onPointerMove=${x} onPointerUp=${()=>p.current=null}></div>
    <p class="muted small">${zs(t)}</p>
  </div>`}function Is(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:A(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:ve(e.end-e.start),color:null}]}function Os(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:A(new Date(e.t*1e3).toISOString()),color:null}]}function zs(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function Bs(e,t,n){let a=null,r=n;for(let o of e){let l=t(o);l<r&&([a,r]=[o,l])}return a}function Vn(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function $t([e,t],n){let a=Math.min(n[1]-n[0],Math.max(60,t-e)),r=Math.max(n[0],Math.min(e,n[1]-a));return[r,r+a]}function Hs(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function Xn(){let e=D(Ne),t=B(null);if(T(()=>{let r=t.current;if(!r||!e)return;r.showModal();let o=()=>Ne.set(null);return r.addEventListener("close",o),()=>r.removeEventListener("close",o)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},a=String(n.props.title??n.props.y??"Chart");return s`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${a} closedby="any">
    <${X.Provider} value=${e.view}><${le} node=${n} /><//>
  </dialog>`}function Yn(e,t){let n=e.toLowerCase(),a=t.toLowerCase();if(!n)return 1;let r=a.indexOf(n);if(r>=0)return 100-Math.min(r,50)-a.length/100;let o=0,l=0;for(let i of a)if(i===n[o]?o++:o>0&&l++,o===n.length)return 40-Math.min(l,39);return 0}function Qn(e){let[t,n]=f(e.query),[a,r]=f(0),o=B(null),l=R(y(ne()).data),i=R(y(We()).data);T(()=>{let c=o.current;c.showModal();let L=()=>q.set(null);c.addEventListener("close",L);let h=!1,I=P=>{let G=c.getBoundingClientRect();return P.clientX<G.left||P.clientX>G.right||P.clientY<G.top||P.clientY>G.bottom},j=P=>h=I(P),K=P=>h&&I(P)&&c.close();return"closedBy"in HTMLDialogElement.prototype||(c.addEventListener("pointerdown",j),c.addEventListener("pointerup",K)),()=>{c.removeEventListener("close",L),c.removeEventListener("pointerdown",j),c.removeEventListener("pointerup",K)}},[]);let m=()=>o.current?.close(),d=c=>()=>_(c),u=W.value,$=u.page==="group"?u.path:".",p=(c,L,h,I)=>({section:"Commands",label:c,detail:L,sym:{icon:h,tone:"muted",label:c},run:I}),x=[...l.map(c=>({section:"Groups",label:c.path==="."?"local":c.path,detail:`${c.runs} runs${c.proposal?` \xB7 ${c.proposal}`:""}`,sym:M("research",c.status),run:d(w(c.path))})),...i.map(c=>({section:"Runs",label:c["run.name"]??c["run.id"],detail:`${c["run.status"]} \xB7 ${c["run.path"]}`,sym:M("run",c["run.status"]),run:d(w(c["run.path"]))})),p("Theme: light","","sun",()=>Re("light")),p("Theme: dark","","moon",()=>Re("dark")),p("Theme: follow the system","","monitor",()=>Re("system")),p("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),p("Show notes and timeline","i","file-text",d(w($,{drawer:!0}))),p("Show or hide the sidebar","\u2318B","panel-left",()=>V.set(!V.value)),p(Q.value?"Resume live updates":"Pause live updates","p",Q.value?"play":"pause",()=>Q.set(!Q.value)),p("Keyboard shortcuts","?","keyboard",()=>oe.set(!0)),p("Settings","","settings",d("/settings/appearance"))].map(c=>({it:c,s:Math.max(Yn(t,c.label),Yn(t,c.detail)*.5)})).filter(c=>c.s>0).sort((c,L)=>L.s-c.s||Jn(c.it.section)-Jn(L.it.section)).slice(0,60).map(c=>c.it),C=c=>{c&&(m(),c.run())},b=c=>{if(c.key==="ArrowDown")r(Math.min(x.length-1,a+1));else if(c.key==="ArrowUp")r(Math.max(0,a-1));else if(c.key==="Enter")C(x[a]);else return;c.preventDefault()},S="";return s`<dialog class="sheet" ref=${o} aria-label="Search" closedby="any">
    <div class="palette-input"><${g} name="search" size=${18} />
      <input autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${x[a]?`pal-${a}`:void 0}
        onInput=${c=>{n(c.target.value),r(0)}} onKeyDown=${b} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${x.map((c,L)=>{let h=c.section!==S&&!t?S=c.section:null;return s`${h?s`<li class="section" role="presentation">${h}</li>`:null}
          <li id=${`pal-${L}`} class="item" role="option" aria-selected=${L===a}
              onMouseMove=${()=>r(L)} onClick=${()=>C(c)}>
            <${E} spec=${c.sym} /><span class="label">${c.label}</span><span class="detail">${c.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function Jn(e){return["Groups","Runs","Commands"].indexOf(e)}function Xe(e,t=[]){let n=new Map,a=(o,l={})=>({path:o,name:o==="."?"local":o.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let o of e)n.set(o.path,a(o.path,o));n.has(".")||n.set(".",a("."));for(let o of t)o.name!=="local"&&(n.has(o.name)||n.set(o.name,a(o.name)),Object.assign(n.get(o.name),{state:o.state,error:o.error}));for(let o of n.values()){if(Y(o.path))continue;let l=o.path.lastIndexOf("/"),i=l<0?".":o.path.slice(0,l);(n.get(i)??n.get(ze(o.path))??n.get(".")).children.push(o)}for(let o of n.values())o.children.sort((l,i)=>l.name.localeCompare(i.name));let r=[...n.values()].filter(o=>o.path!=="."&&Y(o.path)).sort((o,l)=>o.name.localeCompare(l.name));return[n.get("."),...r]}function Zn(e,t,n){let a=[],r=n.toLowerCase(),o=l=>{(!r||l.path.toLowerCase().includes(r)||es(l,r))&&(a.push(l),(r||t.has(l.path)||Y(l.path))&&l.children.forEach(o))};return e.forEach(o),a}function es(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||es(n,t))}function ts(e,t){if(Y(t))return e;let n=t.lastIndexOf("/"),a=n<0?".":t.slice(0,n),r=o=>o.path===a?o:o.children.map(r).find(l=>l)??null;return e.map(r).find(o=>o)?.children??[]}function ns(e){return Y(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function ss(){let e=D(W),t=y(ne()),[n,a]=f(()=>new Set(Ee("open",[]))),[r,o]=f(""),l=B(null),i=e.page==="group"?e.path:null,m=Xe(R(t.data),t.data?.meta?.sources??[]),d=Zn(m,Us(n,i),r),u=(p,v)=>{let x=new Set(n);v??!x.has(p)?x.add(p):x.delete(p),Ce("open",[...x]),a(x)};return s`<nav class="sidebar" aria-label="Groups">
    <label class="filter"><${g} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${r} aria-label="Filter groups"
        onInput=${p=>o(p.target.value)} />
    </label>
    <div class="tree" ref=${l} onKeyDown=${p=>{let v=[...l.current?.querySelectorAll("a.tree-item")??[]],x=v.indexOf(document.activeElement),C=d[x];switch(p.key){case"ArrowDown":v[Math.min(v.length-1,x+1)]?.focus();break;case"ArrowUp":v[Math.max(0,x-1)]?.focus();break;case"ArrowRight":C?.children.length&&u(C.path,!0);break;case"ArrowLeft":C&&n.has(C.path)?u(C.path,!1):C&&v[d.findIndex(b=>b.path===Ks(C.path))]?.focus();break;default:return}p.preventDefault()}} role="tree">
      ${d.map(p=>s`<${As} key=${p.path} node=${p} current=${p.path===i}
        open=${n.has(p.path)||!!r} onToggle=${()=>u(p.path)} />`)}
    </div>
  </nav>`}function As(e){let t=e.node,n=()=>_e(t.path),a=t.children.length>0&&!Y(t.path);return s`<a class=${`tree-item${e.current?" current":""}${t.path.startsWith("@")&&Y(t.path)?" source-root":""}`} href=${w(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${a?e.open:void 0}
      style=${`padding-inline-start:${6+ns(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${r=>{r.metaKey||r.ctrlKey||(r.preventDefault(),_(w(t.path)))}}>
    <span class="twisty" onClick=${r=>{r.preventDefault(),r.stopPropagation(),e.onToggle()}}>
      ${a?s`<${g} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    <span class="tree-name">${t.name}</span>
    ${t.state==="unreachable"?s`<${E} spec=${{icon:"cloud-off",tone:"muted",label:`Unreachable: ${t.error??"no answer"}`}} size=${13} />`:null}
    <span class="tree-marks">
      ${t.running?s`<${E} spec=${M("run","running")} size=${13} />`:null}
      ${t.failed?s`<${E} spec=${{...M("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${13} />`:null}
    </span>
    <span class="count">${t.runs||""}</span>
  </a>`}function Ks(e){if(Y(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function Us(e,t){if(!t||t===".")return e;let n=new Set(e),a=t.split("/");for(let r=1;r<a.length;r++)n.add(a.slice(0,r).join("/"));return n}function rs(){let e=D(W),t=D(V),n=D(q),a=D(oe),r=B(null);T(()=>Ct(()=>r.current),[]),T(()=>(addEventListener("keydown",as),()=>removeEventListener("keydown",as)),[]);let o=e.page==="group"&&e.drawer,l;switch(e.page){case"group":l=s`<${Wn} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":l=s`<${Fn} id=${e.id} />`;break;case"settings":l=s`<${dn} />`;break;case"timeline":l=s`<${qn} key=${e.from} from=${e.from} />`;break;default:l=s`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return re?s`<main class="main render-main" ref=${r}>${l}</main>`:s`<div class=${`shell${t?"":" no-sidebar"}${o?" with-drawer":""}`}>
    <${yn} />
    ${t?s`<${ss} />`:null}
    <main class="main" ref=${r}>${l}</main>
    ${o?s`<${_n} path=${e.path} run=${e.run} />`:null}
    <${wn} />
    ${n!==null?s`<${Qn} query=${n} />`:null}
    ${a?s`<${Gs} />`:null}
    <${Xn} />
  </div>`}function as(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),q.set(q.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),V.set(!V.value);return}if(e.key==="Escape"){if(q.value!==null||oe.value)return;let a=W.value;return a.page==="group"&&a.run?_(w(a.path,{drawer:!0}),{replace:!0}):a.page==="group"&&a.drawer?_(w(a.path),{replace:!0}):void 0}if(t||e.altKey||un(e)||q.value!==null||oe.value)return;let n=W.value;switch(e.key){case"/":e.preventDefault(),q.set("");break;case"?":oe.set(!oe.value);break;case"p":Q.set(!Q.value);break;case"i":n.page==="group"&&_(w(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":V.set(!V.value);break;case"[":case"]":n.page==="group"&&js(n.path,e.key==="]"?1:-1);break}}async function js(e,t){let n=await Le(ne()),a=ts(Xe(R(n),n?.meta?.sources??[]),e),r=a.findIndex(l=>l.path===e),o=a[r+t];o&&_(w(o.path))}function Gs(){let e=B(null);return T(()=>{let t=e.current;t.showModal();let n=()=>oe.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),s`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${Ue.map(([t,n])=>s`<tr><td><kbd>${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 14px"><button class="link" autofocus>Close</button></form>
    </div>
  </dialog>`}Mt();if(re){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(se.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Te.n}en();var Ws=H("meta").then(e=>(re&&(e={...e,settings:{...e.settings,theme_mode:se.value}}),je(e),e));re||wt(async()=>{let[e,t]=await Promise.all([Ws,H("meta")]);e.bundle!==t.bundle?location.reload():je(t)});ft(s`<${rs} />`,document.getElementById("app"));
