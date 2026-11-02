import{$ as re,$a as cn,A as _t,B as Lt,C as Se,Ca as Ge,D as le,Da as C,E as x,Ea as ut,F as Ke,Fa as Gt,G as ce,Ga as mt,H as Re,Ha as Ve,I as be,Ia as qe,J as F,Ja as Vt,K as V,Ka as qt,L as Rt,La as Xt,Ma as Yt,N as D,Na as Jt,O as Pt,P as Ot,Q as de,Qa as Zt,R as Pe,Ra as Qt,S as It,Sa as en,T as Ue,Ta as tn,U as it,Ua as nn,V as ue,Va as sn,W as At,Wa as an,X as lt,Xa as rn,Y as Fe,Z as q,Za as on,_ as ae,_a as ln,aa as je,ab as dn,ba as Kt,bb as un,c as Et,ca as Oe,cb as mn,d as s,da as Ie,db as pn,e as g,eb as $n,f as E,fa as Ut,g as Ct,ga as Ft,h as H,ha as v,i as _e,ia as _,j as ie,ja as We,ka as te,la as O,m as ve,ma as L,n as N,na as ct,o as we,oa as j,p as ke,pa as jt,qa as B,ra as ne,s as A,sa as ze,t as Le,ta as dt,u as xe,ua as Wt,v as ot,va as X,w,wa as he,x as Nt,xa as ye,y as ee,ya as Ee,z as Dt,za as K}from"./chunks/chunk-NUKRIPYV.js";import{a as Tt,b as Mt}from"./chunks/chunk-O2K4N3UR.js";import{e as zt,i as Bt,j as Ht}from"./chunks/chunk-CHIPVRI3.js";import"./chunks/chunk-VC46IEJQ.js";function Ce(e,t){Se(n=>t.includes(n.method)&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var pt=["notes","timeline","groups","check","card","memory_show","status"];async function $t(e,t){let n=e.meta??{};await A("note_add",{group:e.group,type:e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),Ce(e.group,pt)}async function fn(e,t,n,a){await A("note_add",{group:e,type:t,description:n,body:a}),Ce(e,pt)}async function hn(e,t){await A("memory_update",{group:e,body:t}),Ce(e,["memory_show","status"])}async function gn(e,t){let n=await A("proposal_show",{group:e}),a=Object.fromEntries(Object.entries(n.proposal??{}).filter(([r])=>!["schema","author","user","supersedes"].includes(r)));await A("proposal_set",{group:e,proposal:{...a,statement:t}}),Ce(e,["groups","proposal_show","check","summary"])}async function vn(e){await A("note_rm",{note:e.id}),Ce(e.group,pt)}async function bn(e,t,n){await A("name",{run:e,name:n}),Ce(t,["card","runs","groups","summary","series"])}async function Xe(e,t,n){let a=await A("view_text",{path:e,id:t,text:n});return Se(r=>["view","view_history"].includes(r.method)&&r.scope===e),a.id}async function yn(e){await A("view_upgrade",{group:e}),Se(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var Te=new ve(null);async function wn(e,t){return await A("set",{key:e,value:t}),A("meta")}var Y=new ve(we("sidebar",!0)),J=new ve(null),me=new ve(!1),Me=new ve(null);Y.subscribe(e=>ke("sidebar",e));var kn=we("visit",Date.now());ke("visit",Date.now());function xn(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var Ye=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var xs=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function Je(e){Me.set(e),Ue.set(e.theme),e.settings?.theme_mode&&ue.set(e.settings.theme_mode),lt()}var Sn=0;async function ft(e,t){let n=++Sn;e==="theme_mode"&&(ue.set(t),lt());let a=await wn(e,t);n===Sn&&Je(a)}function En(){let e=N(ue),t=re(),n=N(Me),[a,r]=g(null);E(()=>{document.title="Settings \xB7 Beamtime"},[]);let o=(c,u)=>{r(null),ft(c,u).catch(d=>r(d.message))},l=n?.settings??{},i=(c,u,d)=>s`
    <label class="field-label small" for=${`setting-${c}`}>${u}</label>
    <span class="input body">
      <select id=${`setting-${c}`} value=${l[c]} onChange=${p=>o(c,p.target.value)}>
        ${d.map(p=>s`<option value=${p}>${p}</option>`)}
      </select>
    </span>`;return s`<div class="page settings"><div class="sections">
    <${B} label="settings">
      <h1 class="page-title title" tabindex="-1">Settings</h1>
      <p class="muted small">Changes are written to <code>${l.file??"beamtime.yaml"}</code>, the project's settings.</p>
      ${a?s`<${O} kind="error">${a}<//>`:null}
    <//>
    <${B} label="appearance">
      <div class="settings-rows">
        <span class="field-label small">Mode</span>
        <div class="segmented" role="radiogroup" aria-label="Theme mode">
          ${xs.map(([c,u,d])=>s`<button type="button" role="radio" aria-checked=${e===c} onClick=${()=>o("theme_mode",c)}>
            <${v} name=${u} size=${15} />${d}</button>`)}
        </div>
        ${i("theme","Theme",n?.themes??[])}
        ${i("colormap","Colormap",n?.colormaps?.sequential??[])}
        ${i("colormap_diverging","Diverging colormap",n?.colormaps?.diverging??[])}
      </div>
      <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files recolor this layout: they go in <code>themes/</code> next to
        beamtime.yaml. Colormaps color numeric groups and heatmaps.</p>
      ${(n?.theme?.problems??[]).map(c=>s`<${O} kind="warning">${c}<//>`)}
    <//>
    <${B} label="figures">
      <div class="settings-rows">
        <span class="field-label small">Style sheets</span>
        ${(n?.figure_styles??[]).length?s`<${Ge} options=${n.figure_styles} value=${l.figure_style??[]} label="Style sheets"
              placeholder="Add a style" onChange=${c=>o("figure_style",c)} />`:s`<span class="muted small"><code>${JSON.stringify(l.figure_style??[])}</code>; choosing others needs the figures
              extra: <code>uv add matplotlib scienceplots</code></span>`}
      </div>
      <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(l.figure_style??[])})</code>, in this order
        (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
        <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <//>
    <${B} label="keyboard">
      <table class="kv">${Ye.map(([c,u])=>s`<tr><td><kbd class="small">${c}</kbd></td><td>${u}</td></tr>`)}</table>
    <//>
    <${B} label="about">
      <table class="kv">
        <tr><td class="muted">version</td><td>${n?.version}</td></tr>
        <tr><td class="muted">root</td><td><code class="code">${n?.root}</code></td></tr>
        <tr><td class="muted">log dir</td><td><code class="code">${n?.logdir}</code></td></tr>
      </table>
    <//>
  </div></div>`}var oe=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),pe=(e,t=null,n=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{}},scope:e}),ht=e=>({method:"summary",params:{path:e},scope:e}),Ze=e=>({method:"groups",params:{from:e,depth:0},scope:e}),Cn=e=>({method:"check",params:{group:e},scope:e}),Tn=e=>({method:"proposal_show",params:{group:e},scope:e}),Qe=(e,t)=>({method:"card",params:{run:Re(e,t)},scope:t}),Mn=(e,t)=>({method:"output",params:{run:Re(e,t),tail:30},scope:t}),Be=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),et=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),Nn=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),Dn=()=>({method:"status",params:{},scope:"."}),tt=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function He(e){for(let t of[pe(e),Ze(e),Be(e),ht(e)])ot(t);xe(pe(e)).then(t=>{for(let n of _n(t.view))ot(n)}).catch(()=>{})}function _n(e){return e?[...Ss.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(_n)]:[]}var Ss=new Set(["line","custom"]),Ln=e=>({method:"view_history",params:{group:e},scope:e});var Rn={system:"light",light:"dark",dark:"system"},Es={system:"monitor",light:"sun",dark:"moon"};function Pn(){let e=N(Me),t=N(ue),n=N(Y);return s`<header class="topbar">
    <${j} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>Y.set(!n)} />
    <a class="project heading" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>J.set("")} aria-label="Search (⌘K)">
      <${v} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${Cs} />
      <${j} icon=${Es[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${Rn[t]})`}
        onClick=${()=>{ft("theme_mode",Rn[t])}} />
      <a class="icon-button" href=${Ke(V.value.page==="group"?V.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${v} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${v} name="settings" size=${16} /></a>
    </div>
  </header>`}function Cs(){let t=(w(oe()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?s`${[{name:"local",state:"connected"},...t].map(n=>s`<a class=${`source small ${n.state}`}
      href=${x(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${v} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:s`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${v} name="server" size=${15} /> local</span>`}function Ts(e){let[t,n]=g(Date.now());return E(()=>{let a=setInterval(()=>n(Date.now()),e);return()=>clearInterval(a)},[e]),t}function Ms(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function On(){let e=N(Dt),t=N(ee),n=N(_t),a=N(V),r=Ts(5e3),o=w(Dn()).data,l=L(w(tt()).data),i=N(Me),c=o?.daemon,u=o?.runs?.running??0,d=l.filter(R=>R["run.status"]==="failed"&&Ms(R["run.ended_at"])>kn).length,p=o?.meta?.freshness,[y,b,T]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&c?["",`live \xB7 updated ${K(new Date(n).toISOString(),r)}`,`beamtime serve, pid ${c.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return s`<footer class="statusbar small">
    <span class="status-item" data-tip=${T}><span class=${`live-dot ${y}`}></span>${b}</span>
    ${u?s`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>J.set("running")}>
          <${v} name="circle-dot" size=${14} class="tone-accent" />${u} running</button>`:null}
    ${d?s`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>J.set("failed")}>
          <${v} name="circle-x" size=${14} />${d} failed since your last visit</button>`:null}
    ${p?.behind?s`<span class="status-item warn-text" data-tip=${p.text}><${v} name="hourglass" size=${14} />${p.behind} runs behind</span>`:null}
    ${p?.damaged?.length?s`<span class="status-item warn-text" data-tip=${p.damaged.join(`
`)}><${v} name="triangle-alert" size=${14} />${p.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${a.page==="group"&&a.run?s`<span class="status-item"><${v} name="activity" size=${14} />1 run selected</span>`:null}
    <${j} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>ee.set(!t)} />
    ${i?.outdated?s`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item">${i?.version?`beamtime ${i.version}`:""}</span>
  </footer>`}var In=null;function nt(e){let t=H(null),[n,a]=g(null),[r,o]=g(!1),[l,i]=g(!1);E(()=>{let p=!0;return In??=import("./chunks/md-SW3VT2BQ.js"),In.then(y=>y.render(e.text??"")).then(y=>p&&a(y)),()=>{p=!1}},[e.text]),Ct(()=>{let p=t.current;if(!p||!e.clamp)return;let y=()=>i(p.scrollHeight>p.clientHeight+2),b=new ResizeObserver(y);return b.observe(p),()=>b.disconnect()},[e.clamp,n]);let c=e.clamp&&!r,u=`md${c?" clamped":""}`,d=c?`--clamp:${e.clamp}`:"";return s`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?s`<div class=${u} ref=${t} style=${d}>
          ${(e.text??"").split(/\n{2,}/).map(p=>s`<p>${p}</p>`)}
        </div>`:s`<div class=${u} ref=${t} style=${d} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(l||r)?s`<button type="button" class="link small more" onClick=${()=>o(!r)}>${r?"less":"more"}</button>`:null}
  </div>`}function ge(e){let[t,n]=g(!!e.startEditing),[a,r]=g(e.value),[o,l]=g(null),[i,c]=g(null),u=H(null),d=H(!1);E(()=>l(null),[e.value]),E(()=>{!t||!u.current||(u.current.focus(),e.startEditing?u.current.select():u.current.setSelectionRange(u.current.value.length,u.current.value.length))},[t]);let[p,y]=g(!1),b=e.locked??void 0,T=f=>{if(!f.target.closest("a, button, input, summary")){if(b)return y(!0);f.preventDefault(),r(o??e.value),c(null),d.current=!1,n(!0)}},R=()=>{d.current=!0,n(!1),c(null),e.onCancel?.()},$=async()=>{if(d.current)return;d.current=!0;let f=e.multiline?a.trim():a.replace(/\s*\n\s*/g," ").trim();if(f===e.value.trim()||!f&&!e.multiline)return R();n(!1),l(f);try{await e.onSave(f)}catch(h){l(null),r(f),c(h.message),d.current=!1,n(!0)}},k=f=>{if(f.key==="Escape")return f.preventDefault(),f.stopPropagation(),R();f.key!=="Enter"||f.isComposing||f.keyCode===229||(!e.multiline||f.metaKey||f.ctrlKey)&&(f.preventDefault(),$())};if(t)return s`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${u} class="edit-field" value=${a} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,a.split(`
`).length+1)):1}
        onInput=${f=>r(f.target.value)} onKeyDown=${k} onBlur=${$}></textarea>
      <span class="edit-hint small">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${i?s` · <span class="bad-text">${i}</span>`:null}</span>
    </div>`;let m=o??e.value;return s`<div class=${`editable${b?" locked":""}${o!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${b?`${e.label}: ${b}`:`Edit ${e.label}`}
      data-tip=${b} onClick=${T} onBlur=${()=>y(!1)}
      onKeyDown=${f=>f.key==="Enter"&&f.target===f.currentTarget&&T(f)}>
    ${m.trim()?e.render?e.render(m):m:s`<span class="muted">${e.placeholder??"Click to write"}</span>`}
    ${p&&b?s`<span class="edit-hint small locked-why" role="status"><${v} name="lock" size=${14} /> ${b}</span>`:null}
  </div>`}function gt(e){let t=[];if(e.effect!==void 0&&e.effect!==null){let n=e.ci?` [${X(e.ci[0])}, ${X(e.ci[1])}]`:"";t.push(`${e.effect>=0?"+":""}${X(e.effect)}${n}`)}return e.threshold!==void 0&&e.threshold!==null&&t.push(`needs ${e.op} ${X(e.threshold)}`),e.points&&t.push(`${e.points} point${e.points>1?"s":""}`),e.detail&&t.push(e.detail),t.join(" \xB7 ")}function vt(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function zn({node:e}){let t=ae("proposal"),n=ae("check"),a=t.data,r=n.data;if(!a)return s`<${te} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let o=a.proposal??{},l=(a.versions??[]).filter(c=>c.version!==a.version),i=!e.props.of||e.props.of===".";return s`<${te} title="Predictions" result=${t} class="proposal">
    ${i?null:s`<p class="statement">${o.statement}</p>`}
    ${o.rationale?s`<p class="rationale prose">${o.rationale}</p>`:null}
    <div class="predictions">
      ${(r?.predictions??[]).map(c=>s`<div class="prediction" key=${c.name}>
          <${_} spec=${C("result",c.result)} />
          <span class="pname">${c.name}</span>
          <span class="pdetail num small">${gt(c)}</span>
        </div>`)}
    </div>
    ${l.length?s`<${dt} summary=${`${l.length} earlier version${l.length>1?"s":""}`}>
          ${l.map(c=>s`<p class="small"><code>${c.version}</code> ${c.statement}
            <span class="muted">(${c.runs} runs, check ${c.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function Bn({node:e}){let t=ae("main"),n=e.data?.main.params.group??".",a=t.data?.chain??[],r=a.find(i=>i.group===n)??null,o=a.filter(i=>i.group!==n),l=r?.notes_since?"out of date":r?`version ${r.versions??1}`:"none yet";return s`<${ct} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?l:void 0} open=${!1} result=${t}
      action=${s`<${_} spec=${{icon:"circle-help",tone:"muted",label:Ds}} />`}>
    <${ge} value=${r?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${i=>s`<${nt} text=${i} />`} onSave=${i=>hn(n,i)} />
    ${r&&(r.body?.length>(t.data?.budget??1/0)||r.notes_since>=Ns)?s`<p class="memory-meta small warn-text">${r.body?.length>t.data.budget?`${r.body.length} characters, beyond the budget of ${t.data.budget}`:`${r.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${r?s`<p class="memory-meta small">${r.author} · covers notes until ${r.covers_until?.slice(0,10)}
          ${r.notes_since?s` · <span class="warn-text">${r.notes_since} newer note${r.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${o.length?s`<p class="memory-meta small">Memory above this group: ${o.map((i,c)=>s`${c?", ":""}<a href=${x(i.group)}>${i.group==="."?"local":i.group}</a>`)}</p>`:null}
  <//>`}var Ns=5,Ds="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",_s="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function Hn({node:e}){let t=ae("main"),n=e.data?.main.params.from??".",a=L(t.data).filter(r=>r.path!==n);return s`<${te} title=${e.props.title} count=${t.data?String(a.length):void 0} result=${t}>
    ${t.data&&!a.length?s`<${O}>No groups below.<//>`:null}
    <div class="group-list">
      ${a.map(r=>{let[o,l]=vt(r.progress),i=(r.failed??0)+(r.killed??0)+(r.lost??0);return s`<a class="group-row" key=${r.path} href=${x(r.path)}
            onPointerEnter=${()=>He(r.path)} onFocus=${()=>He(r.path)}>
          <${_} spec=${C("research",r.status)} />
          <span class="gname heading">${r.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${r.status!=="concluded"?s`<span class=${`tone-${C("research",r.status).tone}`}>${C("research",r.status).label}</span>`:null}
            ${r.check?s`<${_} spec=${C("result",r.check)} word />`:null}
            ${r.verdict?s`<${_} spec=${C("verdict",r.verdict)} />`:null}
            ${o?s`<span data-tip=${l}>${o}</span>`:null}
            <span class="num"><b>${r.runs}</b> runs</span>
            ${r.running?s`<${_} spec=${C("run","running")} />`:null}
            ${i?s`<span class="tone-bad num" data-tip="failed, killed or lost"><${v} name="circle-x" size=${14} /> ${i}</span>`:null}
          </span>
          ${r.proposal?s`<span class="gstatement caption">${r.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function An({node:e}){let t=ae("main"),n=e.data?.main.params.from??".",[a,r]=g(!1),o=(t.data?.entries??[]).filter(i=>!String(i.state??"").startsWith("superseded")),l=t.data?.meta?.matched??o.length;return s`<${ct} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(l):void 0} result=${t}
      action=${s`<${_} spec=${{icon:"circle-help",tone:"muted",label:_s}} />
        ${s`<${j} icon="plus" label="Add a note" onClick=${()=>r(!0)} />`}`}>
    <div class="notes">
      ${a?s`<${Ps} group=${n} onDone=${()=>r(!1)} />`:null}
      ${t.data&&!o.length&&!a?s`<p class="muted small">No notes yet.</p>`:null}
      ${o.map(i=>s`<${st} key=${i.id} note=${i} scope=${n} />`)}
      ${t.data?.more&&e.data?s`<${Kn} call=${e.data.main} before=${o[o.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var Ls=20;function Kn(e){let[t,n]=g(!1),a=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:Ls}}:null,r=w(a);if(!t)return s`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(r.status==="error")return s`<p class="bad-text small">${r.error}</p>`;let o=r.data?.entries??[];return s`${r.data?null:s`<div class="skeleton" style="block-size: 40px"></div>`}
    ${o.map(l=>s`<${st} key=${l.id} note=${l} scope=${e.scope} />`)}
    ${r.data?.more?s`<${Kn} call=${e.call} before=${o[o.length-1]?.id} scope=${e.scope} />`:null}`}var Rs=["observation","idea","question","decision"];function Ps(e){let[t,n]=g("observation"),[a,r]=g(""),[o,l]=g(""),[i,c]=g(null),[u,d]=g(!1),p=async b=>{if(b.preventDefault(),!a.trim())return c("give the note a title");d(!0);try{await fn(e.group,t,a.trim(),o.trim()),e.onDone()}catch(T){c(T.message),d(!1)}};return s`<form class="note new-note" onSubmit=${p} onKeyDown=${b=>{b.key==="Escape"&&e.onDone(),b.key==="Enter"&&(b.metaKey||b.ctrlKey)&&p(b)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${t} aria-label="Note type" onChange=${b=>n(b.target.value)}>
        ${Rs.map(b=>s`<option value=${b}>${b}</option>`)}
      </select></span>
      <span class="input body new-note-field"><input class="new-note-title" value=${a} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${b=>r(b.target.value)} /></span>
    </div>
    <span class="input small"><textarea class="new-note-body" rows="4" value=${o} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${b=>l(b.target.value)}></textarea></span>
    <div class="save-actions">
      <${ne} type="submit" icon=${u?"hourglass":"plus"} disabled=${u}>${u?"Adding\u2026":"Add note"}<//>
      <${ne} icon="x" kind="quiet" onClick=${e.onDone}>Cancel<//>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${i?s`<span class="bad-text small">${i}</span>`:null}
    </div>
  </form>`}function st(e){let t=e.note,[n,a]=g(!!e.open),[r,o]=g(!1),l=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,i=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),c=t.meta?.author;return s`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${u=>!u.target.closest(".editable, a, .note-delete")&&a(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${v} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${_} spec=${C("note",t.type)} />
      <${ge} value=${t.description} label="the note's title" class="note-title heading" render=${Is}
        onSave=${u=>$t(t,{description:u})} />
      ${t.overall?s`<${_} spec=${C("verdict",t.overall)} />`:null}
      ${t.state?s`<${jt} tone="warn">${t.state}<//>`:null}
      ${l?s`<a class="note-group small" href=${x(l)} data-tip="from this group">${Os(l,e.scope)}</a>`:null}
      <span class="note-meta small">${c?`${c} \xB7 `:""}${K(i)}</span>
      ${s`<${j} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${r}
        onClick=${u=>{u.stopPropagation(),o(!r)}} />`}
    </div>
    ${r?s`<div class="note-confirm small" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <${ne} icon="trash" kind="danger" onClick=${()=>{vn(t)}}>Delete<//>
          <${ne} icon="x" kind="quiet" onClick=${()=>o(!1)}>Cancel<//>
        </div>`:null}
    ${n?s`<${ge} value=${t.body??""} label="the note" multiline class="note-body prose markdown"
          placeholder="Add details in Markdown" render=${u=>s`<${nt} text=${u} />`}
          onSave=${u=>$t(t,{body:u})} />`:null}
  </article>`}function Os(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,a=n.split("/").pop()??n;return le(a)?a.slice(-8):n}function Un({node:e}){let t=ae("main"),n=t.data?.lines??[],a=t.data?.meta??{},r=s`<${v} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${a.total_lines??n.length} lines${(a.shown??0)<(a.total_lines??0)?`, last ${a.shown}`:""}`:""}</span>`;return s`<${te} result=${t}>
    <${dt} summary=${r} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function Fn({node:e}){let t=ie(q);return s`<${te} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${ge} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${Te.value===e.id} onCancel=${()=>Te.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>s`<${nt} text=${n} />`}
      onSave=${n=>(Te.set(null),Xe(t.path,e.id,n))} />
  <//>`}function jn({node:e}){return s`<${O} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function Is(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let a=n.slice(2,-2),[r]=a.split(/[#@]/),o=r.split("/").pop()??"";return s`<a href=${le(o)?ce(o):x(r)}>${a}</a>`}return n.startsWith("`")?s`<code>${n.slice(1,-1)}</code>`:n})}function Wn(e){let t=()=>D(x(e.path),{replace:!0});return s`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${v} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${j} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?s`<${zs} id=${e.run} scope=${e.path} />`:s`<${Bs} path=${e.path} />`}
  </aside>`}function zs({id:e,scope:t}){let n=w(Qe(e,t)).data,a=w(Mn(e,t)).data,r=w(Be(t)).data,o=re(),l=_e(()=>je(L(r).map(d=>d["run.id"]),o).get(e),[r,o,e]);if(!n)return s`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let i=n.run,c=Object.entries(n.metrics??{}),u=zt(l,o);return s`<div class="drawer-body">
    <h3 class="heading"><span class=${u.class} style=${u.style}></span>
      <a href=${ce(e)}>${i.name}</a></h3>
    <p class="facts small">
      <${_} spec=${C("run",i.status)} word />
      <span><b>${ye(i.steps)}</b> steps</span>
      <span><b>${Ee(i.duration_s)}</b></span>
      <span data-tip=${i.created_at}>${K(i.created_at)}</span>
    </p>
    ${i.error?s`<pre class="log code bad-text">${i.error}</pre>`:null}
    <h4 class="small">Config</h4>
    <table class="kv small">${Object.entries(n.config??{}).map(([d,p])=>s`<tr><td>${d}</td><td class="num">${X(p)}</td></tr>`)}</table>
    ${c.length?s`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${c.map(([d,p])=>s`<tr><td>${d}</td><td class="num"><b>${X(p.last)}</b></td>
              <td class="num">${X(p.min)}</td><td class="num">${X(p.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?s`<h4 class="small">Cited by</h4>${n.cited_by.map(d=>s`<p class="small"><${_} spec=${C("note",d.type)} /> ${d.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(d=>s`<div class="event small"><span class="muted num">${d.t?.slice(5,16).replace("T"," ")}</span>
        <${v} name=${ut(d.type)} size=${14} /><span>${d.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(a?.lines??[]).join(`
`)}</pre>
  </div>`}function Bs({path:e}){let t=w(et(e)).data,n=w(Nn(e)).data;return s`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?s`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(a=>!String(a.state??"").startsWith("superseded")).map(a=>s`<${st} key=${a.id} note=${a} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(a=>s`<div class="event small"><span class="muted num">${a.t?.slice(5,16).replace("T"," ")}</span>
        <${v} name=${a.kind==="note"?"file-text":ut(a.type)} size=${14} />
        <span>${a.run?s`<a href=${ce(a.run)}>${a.run.slice(-8)}</a> `:null}${a.description??a.type}</span></div>`)}
  </div>`}var bt=["failed","killed","lost"];function yt(e){let t=be(e.path),n=t==="."?e.path:e.path.slice(t.length+1),a=F(e.path)?[]:n.split("/"),r=a.length&&le(a[a.length-1])?a[a.length-1]:null,o=a.slice(0,-1),l=i=>[...t==="."?[]:[t],...o.slice(0,i+1)].join("/");return s`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${a.length?s`<a href=${x(t)}>${t==="."?"local":t}</a>`:null}
      ${o.map((i,c)=>s`<span>/</span><a href=${x(l(c))}>${i}</a>`)}
    </nav>
    ${r?s`<${Ks} id=${r} scope=${e.path} />`:s`<${Hs} path=${e.path} />`}
    ${e.finding?s`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function Hs({path:e}){let t=L(w(Ze(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return s`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=bt.reduce((r,o)=>r+(t[o]??0),0);return s`
    <h1 class="page-title title" tabindex="-1">${n} <${_} spec=${C("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?s`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?s`<span><b>${t.finished}</b> finished</span>`:null}
      ${a?s`<span class="tone-bad" data-tip=${bt.filter(r=>t[r]).map(r=>`${t[r]} ${r}`).join(", ")}>
            <${v} name="circle-x" size=${15} /> <b>${a}</b> ${a===1?bt.find(r=>t[r]):"ended early"}</span>`:null}
      ${t.notes?s`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${Vn} path=${e} />
    </p>`}function Gn({path:e}){let t=L(w(Ze(e)).data)[0]??null,n=w(t?.proposal?Cn(e):null).data,a=w(t?.proposal?Tn(e):null).data;if(!t?.proposal)return null;let r=a?.proposal?.rationale,o=a?.versions?.find(c=>c.version===a.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[l,i]=vt(n?.progress?.text??t.progress);return s`<${B} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${ge} value=${t.proposal} label="the proposal's statement" locked=${a?o:"Loading the proposal\u2026"}
          render=${c=>s`<span data-tip=${o?void 0:r}>${c}</span>`}
          onSave=${c=>gn(e,c)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(c=>{let u=C("result",c.result),d=gt(c),p=d?`${u.label}: ${d}`:u.label;return s`<span class=${`check small tone-${u.tone}`} key=${c.name} data-tip=${p}
              aria-label=${`${c.name}: ${p}`} tabindex="0"><${v} name=${u.icon} size=${14} />${c.name}</span>`})}
        ${n?.provisional||l?s`<span class="small">
              ${n?.provisional?s`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${l?s`<span class="muted" data-tip=${i}>${n?.provisional?" \xB7 ":""}${l}</span>`:null}
            </span>`:null}
      </div>
      <${As} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function As(e){let t=w(e.verdict?et(e.path):null).data;if(!e.verdict)return s`<p class="verdict-line muted">no verdict yet</p>`;let n=C("verdict",e.verdict),a=(t?.entries??[]).find(o=>o.type==="verdict"&&(o.group??e.path)===e.path),r=a?he(a.id):null;return s`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${v} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${a?s`<span class="small muted" data-tip=${r}>verdict${a.meta?.author?` by ${a.meta.author}`:""}${r?` \xB7 ${K(r)}`:""}</span>`:null}
  </p>`}function Ks({id:e,scope:t}){let n=w(Qe(e,t)).data;if(!n)return s`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=n.run,r=()=>{navigator.clipboard?.writeText(a.id)};return s`
    <h1 class="page-title title" tabindex="-1"><${ge} value=${a.name??a.id} label="the run's name" class="title-edit"
        onSave=${o=>bn(a.id,t,o.trim())} />
      <${_} spec=${C("run",a.status)} word /></h1>
    ${a.error?s`<p class="bad-text" data-tip=${a.error}>${a.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${ye(a.steps)}</b> steps</span>
      <span><b>${Ee(a.duration_s)}</b></span>
      <span data-tip=${a.created_at}>${K(a.created_at)}</span>
      <${Vn} path=${t} />
      <${j} icon="copy" label=${`Copy the run id ${a.id}`} onClick=${r} />
      <${Wt} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${Us(a).map(([o,l])=>s`<tr><td class="muted">${o}</td><td>${l}</td></tr>`)}</table>
        <div class="menu-list">
          <button type="button" onClick=${()=>D(x(t,{run:a.id}),{replace:!0})}>
            <${v} name="panel-right" size=${15} /> Open in the side panel</button>
          <button type="button" onClick=${r}><${v} name="copy" size=${15} /> Copy the run id</button>
          ${a.git?.commit?s`<button type="button" onClick=${()=>navigator.clipboard?.writeText(a.git.commit)}>
            <${v} name="git-commit" size=${15} /> Copy the commit</button>`:null}
        </div>
      <//>
    </div>
    ${(n.proposals??[]).length?s`<div class="checks">
          ${n.proposals.map(o=>{let l=C("result",o.check);return s`<a class=${`check small tone-${l.tone}`} href=${x(o.group)} data-tip=${o.statement}>
              <${v} name=${l.icon} size=${14} />${o.group==="."?"own proposal":o.group}
              ${o.verdict?s`<${_} spec=${C("verdict",o.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function Vn({path:e}){let t=w(ht(e)).data?.summary;if(!t)return null;let n=Object.entries(t.config??{}).map(([r,o])=>`${r} ${X(o)}`).join(", "),a=le(e.split("/").pop()??"");return s`<span data-tip=${`${t.stat} of ${t.metric} over ${a?"the run":"all runs"}`}>
    best <b>${t.metric} ${X(t.value)}</b>
    ${a?null:s` · <a href=${ce(t.run)}>${t.name}</a>${n?s` <em>(${n})</em>`:null}`}
  </span>`}function Us(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,a])=>[n,String(a)])}var qn=15e3;function Xn({node:e}){let t=ie(q),n=re(),[a,r]=Kt(),o=e.props.code,l=w(r&&o?{method:"code",params:o,scope:t.path}:null),[i,c]=g(null),[u,d]=g(120),[p,y]=g({error:null,warnings:[]}),b=$=>{de&&console.error(`[block ${e.id}] ${$}`),y(k=>({...k,error:$}))};E(()=>{let $=i?.contentWindow;if(!$||l.status!=="ready")return;let k=z=>$.postMessage(z,"*"),m=new Map,f=new en,h=!0;Le.n++;let I=()=>{h&&Le.n--,h=!1},W=setTimeout(()=>{h&&b(`no first render within ${qn/1e3} s`),I()},qn),U=z=>{if(z.source!==$)return;let S=z.data;switch(S.type){case"hello":k({type:"init",init:{id:e.id,code:l.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:At.value,pair:Ue.value,prefs:mt(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics}});break;case"sub":if(!Jt.has(S.call.method)){k({type:"result",id:S.id,result:{status:"error",data:null,error:`${S.call.method} is not available in a custom block`,refreshing:!1}});break}m.get(S.id)?.(),m.set(S.id,Nt(S.call,De=>k({type:"result",id:S.id,result:De})));break;case"unsub":m.get(S.id)?.(),m.delete(S.id);break;case"navigate":S.url.startsWith("/")&&D(S.url);break;case"height":f.accept(performance.now())?d(Math.max(40,S.height)):P("its height keeps changing, so it is fixed at its last height");break;case"ready":y(De=>({...De,blank:S.blank,overflow:S.overflow})),I();break;case"warn":P(S.message);break;case"hover":it.set(S.run);break;case"prefs":JSON.stringify(M.value)!==JSON.stringify(S.prefs)&&M.set(S.prefs);break;case"download":case"snapshot":S.href?Zt(S.href,S.name)?performance.now()-G>1e3&&(G=performance.now(),Ie().download(S.href,S.name)):P(`a download of ${S.name} was refused: only PNG, SVG and CSV files`):P("it draws no SVG or canvas to download");break;case"figure":Ie().figure(S.spec,S.name).catch(De=>P(`the PDF failed: ${De.message}`));break;case"expand":Qt(S.node)&&Ie().expand(S.node,t);break;case"error":b(S.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,T)),I();break;default:break}},P=z=>{de&&console.warn(`[block ${e.id}] ${z}`),y(S=>S.warnings.includes(z)?S:{...S,warnings:[...S.warnings,z]})},G=-1/0,M=mt(t.path),Q=it.subscribe(z=>k({type:"hover",run:z})),fe=M.subscribe(z=>k({type:"prefs",prefs:z}));return addEventListener("message",U),k({type:"ping"}),()=>{Q(),fe(),removeEventListener("message",U),clearTimeout(W);for(let z of m.values())z();I()}},[l.status,l.data,i]),E(()=>{let $={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};i?.contentWindow?.postMessage($,"*")},[t.names,t.colors,t.metrics,i]),E(()=>{n&&i?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let T=typeof o=="object"?o.path??o.block:String(o??"");Ut(e.id,{png:()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")});let R=r&&l.status==="ready"&&!p.error;return s`<div ref=${a} class="custom-block">
    <div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${R?s`<span class="chart-tools">
            <${j} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?s`<${j} icon="x" label="Close (Esc)" onClick=${()=>Oe.set(null)} />`:s`<${j} icon="maximize" label="Expand" onClick=${()=>Ie().expand(e,t)} />`}
          </span>`:null}
    </div>
    <${te} caption=${e.props.expanded?void 0:e.props.caption} result=${l}>
      ${p.error?s`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${T})</span>
            <pre class="code">${p.error}</pre>
          </div>`:null}
      ${p.warnings.map($=>s`<${O} kind="warning">${$}<//>`)}
      ${R?s`<div class="custom-frame" data-frame-blank=${p.blank?"1":void 0} data-frame-overflow=${p.overflow?"1":void 0}>
            <iframe key=${l.data.code} ref=${c} sandbox="allow-scripts" ...${Fs()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${u}px`} />
          </div>`:null}
    <//>
  </div>`}function Fs(){if(!!1)return{src:Tt("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1").replace(/@font-face\s*\{[^}]*\}/g,""),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}function Yn({node:e}){let t=ae("main"),n=ie(q),a=t.data?.entries??[];return s`<${te} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!a.length?s`<${O}>No images logged.<//>`:null}
    <div class="images">
      ${a.map(r=>s`<figure key=${`${r.run}/${r.path}`}>
          <img src=${Mt(Re(r.run,n.path),r.path)} alt=${r.caption??e.props.title} loading=${Pe?"eager":"lazy"} />
          <figcaption class="small">step ${ye(r.step)}${r.caption?` \xB7 ${r.caption}`:""}</figcaption>
        </figure>`)}
    </div>
  <//>`}function Jn({node:e}){let t=ae("main"),n=t.data?.entries??[];return s`<${te} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?s`<${O}>No text logged.<//>`:null}
    ${n.map(a=>s`<div class="text-entry" key=${`${a.run}/${a.step}`}>
        <div class="muted small">step ${ye(a.step)}${a.caption?` \xB7 ${a.caption}`:""}</div>
        <pre class="code">${a.text??""}</pre>
      </div>`)}
  <//>`}function Zn({node:e}){let[t,n]=g(Pe||e.props.open!==!1),a=s`${(e.children??[]).map(l=>s`<${se} key=${l.id} node=${l} />`)}`,r=ie(We);if(!e.props.title)return s`<div class="stack">${a}</div>`;let o=r===e.props.title.toLowerCase();return s`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${t} aria-label=${o?`${t?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${()=>n(!t)}>
      <${v} name=${t?"chevron-down":"chevron-right"} size=${16} />${o?null:e.props.title}
    </button>
    ${t?s`<div class="stack">${a}</div>`:null}
  </div>`}function Qn({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return s`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>s`<${se} key=${n.id} node=${n} />`)}
  </div>`}function es({node:e}){let t=ie(q),n=Ve(t.path),a=e.props.min_width??320,r=e.props.columns,o=r?`grid-template-columns: repeat(${r}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${a}px, 100%), 1fr))`,l=(e.children??[]).flatMap(d=>d.props.y??[]),i=e.props.addable?n.added.filter(d=>!l.includes(d)).map(d=>({block:"line",id:`added-${d}`,props:{y:d,added:!0},data:{main:{...e.props.template,params:{...e.props.template.params,y:[d]}}}})):[],c=Yt([...e.children??[],...i],n.order[e.id]),u=(d,p)=>{let y=c.map(b=>b.id).filter(b=>b!==d);y.splice(y.indexOf(p),0,d),qt(t.path,e.id,y)};return s`<div class="grid" style=${o}>
    ${c.map(d=>s`<${js} key=${d.id} node=${d} path=${t.path} span=${n.spans[d.id]??d.props.span??1}
      columns=${r} onDrop=${p=>p!==d.id&&u(p,d.id)} />`)}
    ${e.props.addable&&!!1?s`<${Ws} path=${t.path} shown=${[...l,...n.added]} />`:null}
  </div>`}var wt=[1,2,"full"];function js(e){let[t,n]=g(!1),a=wt[(wt.indexOf(e.span)+1)%wt.length],r=o=>o==="full"?"full width":`${o} column${o===1?"":"s"}`;return s`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${o=>{o.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${o=>{o.preventDefault(),n(!1),e.onDrop(o.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${o=>o.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${v} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${r(e.span)}; click for ${r(a)}`}
        aria-label=${`Width ${r(e.span)}`} onClick=${()=>Xt(e.path,e.node.id,a)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${se} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function Ws(e){let t=w({method:"keys",params:{from:e.path},scope:e.path}).data,n=(t?.metrics?.rows??[]).map(a=>a[0]).filter(a=>!e.shown.includes(a));return t&&!n.length?null:s`<div class="add-chart">
    <span class="add-chart-label"><${v} name="plus" size=${16} /> Add a chart</span>
    <${Ge} single options=${n} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
      onChange=${([a])=>qe(e.path,r=>({added:[...r.added,a]}))} />
  </div>`}function ts({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[a,r]=g(()=>t.find(i=>i.id===n())?.id??t[0]?.id),o=i=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(i)}`),r(i)},l=t.find(i=>i.id===a)??t[0];return Pe?s`<div class="stack">${t.map(i=>s`<${se} key=${i.id} node=${i} />`)}</div>`:s`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(i=>s`<button type="button" role="tab" id=${`tab-${i.id}`} aria-selected=${i.id===l?.id}
          aria-controls=${`panel-${i.id}`} onClick=${()=>o(i.id)}>${i.props.title??i.id}</button>`)}
    </div>
    ${l?s`<div class="stack" role="tabpanel" id=${`panel-${l.id}`} aria-labelledby=${`tab-${l.id}`}>
          ${(l.children??[]).map(i=>s`<${se} key=${i.id} node=${i} />`)}
        </div>`:null}
  </div>`}var Gs={section:Zn,row:Qn,grid:es,line:ln,table:pn,stat:mn,images:Yn,text:Jn,proposal:zn,note:jn,output:Un,memory:Bn,groups:Hn,notes:An,tabs:ts,scatter:cn,bar:dn,histogram:un,data_table:sn,timeline:an,custom:Xn,markdown:Fn};function se({node:e}){return s`<${Gt} node=${e} blocks=${Gs} />`}function ns(e,t){let n=e.split(`
`),a=t.split(`
`),r=n.length,o=a.length,l=Array.from({length:r+1},()=>new Uint32Array(o+1));for(let d=r-1;d>=0;d--)for(let p=o-1;p>=0;p--)l[d][p]=n[d]===a[p]?l[d+1][p+1]+1:Math.max(l[d+1][p],l[d][p+1]);let i=[],c=0,u=0;for(;c<r&&u<o;)n[c]===a[u]?(i.push({kind:"same",text:n[c]}),c++,u++):l[c+1][u]>=l[c][u+1]?i.push({kind:"removed",text:n[c++]}):i.push({kind:"added",text:a[u++]});for(;c<r;)i.push({kind:"removed",text:n[c++]});for(;u<o;)i.push({kind:"added",text:a[u++]});return i}function ss(e,t=3){let n=[],a=0;for(;a<e.length;){if(e[a].kind!=="same"){n.push(e[a++]);continue}let r=a;for(;r<e.length&&e[r].kind==="same";)r++;let o=a===0?0:t,l=r===e.length?0:t;r-a>o+l+1?n.push(...e.slice(a,a+o),{kind:"skip",count:r-a-o-l},...e.slice(r-l,r)):n.push(...e.slice(a,r)),a=r}return n}var kt={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",timeline:"timeline",proposal:"predictions"};function as(e){if(kt[e.block])return kt[e.block];if(e.block==="row"||e.block==="grid"){if(e.props.addable)return"charts";let n=new Set((e.children??[]).map(r=>kt[r.block])),[a]=n;if(n.size===1&&a)return a}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function at(e){let t=w(Be(e.path)),n=re(),a=L(t.data),r=_e(()=>je(a.map(d=>d["run.id"]),n),[t.data,n]),o=_e(()=>new Map(a.map(d=>[d["run.id"],d["run.name"]??d["run.id"]])),[t.data]),l=e.plain?"view plain":"sections view";if(!e.view)return s`<div class=${l}>${e.before}
      ${e.plain?s`<div class="skeleton late" style="block-size: 320px"></div>`:s`<${B} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let i={path:e.path,colors:r,names:o,metrics:e.view.metrics??{}},c=e.view.view;if(e.plain)return s`<div class=${l}><${q.Provider} value=${i}><${se} node=${c} /><//></div>`;let u=c.block==="section"&&!c.props.title?c.children??[]:[c];return s`<div class=${l}>${e.before}
    <${q.Provider} value=${i}>
      ${u.map(d=>{let p=as(d);return s`<${B} key=${d.id} label=${p}><${We.Provider} value=${p}><${se} node=${d} /><//><//>`})}
    <//>
  </div>`}function rs(e){if(null)return s`<div class="view-source small"><${v} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=N(V),a=n.page==="group"&&n.version,r=t.versions?s`<a href=${x(e.path,{history:!0})}><${v} name="history" size=${14} /> history (${t.versions})</a>`:null,o;switch(t.source){case"draft":o=s`draft <b>${t.draft}</b>`;break;case"view":o=s`${t.title?s`<em>${t.title}</em> · `:null}saved ${K(he(t.version))} by ${t.author??"unknown"}`;break;default:o=s`the built-in view`}return s`<div class="view-source small">
    <${v} name="layout" size=${14} /><span>${o}</span>
    ${a?s`<a href=${x(e.path)}>an older version · show the current one</a>`:null}
    ${r}
    ${t.outdated?.length&&!a?s`<${Vs} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||a?null:s`<${qs} path=${e.path} />
        <${Xs} path=${e.path} view=${t} />`}
  </div>`}function Vs(e){let[t,n]=g(null),a=e.outdated.map(o=>o.name).join(", ");return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{await yn(e.path)}catch(o){n(o.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${a} exists; update re-pins this view to it (a new version)`}>
      <${v} name="update" size=${14} /> update ${a}</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function qs(e){let[t,n]=g(null);return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{Te.set(await Xe(e.path,null,""))}catch(r){n(r.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${v} name="file-text" size=${14} /> add text</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function Xs(e){let t=Ve(e.path),n=Vt(t),[a,r]=g(!1),[o,l]=g(e.view.title??""),[i,c]=g(e.view.finding??""),[u,d]=g(null),[p,y]=g(!1);if(!n&&!a)return null;let b=async T=>{T.preventDefault(),y(!0),d(null);try{let R={charts:t.charts,added:t.added,order:t.order,spans:t.spans};await A("save_view",{path:e.path,prefs:R,title:o,finding:i}),qe(e.path,()=>({view:{},charts:{},added:[],order:{},spans:{}})),Se($=>["view","view_history","summary"].includes($.method)&&$.scope===e.path),r(!1)}catch(R){d(R.message)}finally{y(!1)}};return a?s`<form class="save-form" onSubmit=${b}>
    <${ze} label="Title"><input value=${o} onInput=${T=>l(T.target.value)} /><//>
    <${ze} label="Finding"><input value=${i} placeholder="the key result in one sentence"
        onInput=${T=>c(T.target.value)} /><//>
    <div class="save-actions">
      <${ne} type="submit" icon=${p?"hourglass":"save"} disabled=${p}>${p?"Saving\u2026":"Save as view"}<//>
      <${ne} icon="x" kind="quiet" onClick=${()=>r(!1)}>Cancel<//>
      ${u?s`<span class="bad-text small">${u}</span>`:null}
    </div>
  </form>`:s`<${ne} icon="save" class="save-view" onClick=${()=>r(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function os(e){let t=w(Ln(e.path)),n=t.data?.entries??[],[a,r]=g(null),o=a??n.slice(0,2).map(i=>i.version).reverse(),l=i=>{let c=o.includes(i)?o.filter(u=>u!==i):[...o,i].slice(-2);r(c.sort())};return t.status==="error"?s`<${O} kind="error">${t.error}<//>`:s`<section class="history">
    <h2 class="history-title heading"><${v} name="history" size=${16} /> View history</h2>
    ${t.data&&!n.length?s`<${O}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((i,c)=>s`<li key=${i.version} class=${o.includes(i.version)?"picked":""}>
          <label><input type="checkbox" checked=${o.includes(i.version)} onChange=${()=>l(i.version)} />
            <span class="num muted" data-tip=${i.version}>${K(i.time)}</span>
            <b>${i.title??"untitled"}</b><span class="muted">${i.author??""}</span>
            ${i.message?s`<span>${i.message}</span>`:null}</label>
          <a href=${c===0?x(e.path):x(e.path,{version:i.version})}
            onClick=${u=>{u.preventDefault(),D(c===0?x(e.path):x(e.path,{version:i.version}))}}>${c===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${o.length===2?s`<${Ys} path=${e.path} a=${o[0]} b=${o[1]} />`:null}
  </section>`}function Ys(e){let t=i=>({method:"view_show",params:{group:e.path,version:i},scope:e.path}),n=w(t(e.a)).data,a=w(t(e.b)).data,r=w(pe(e.path,e.a)).data,o=w(pe(e.path,e.b)).data,l=n&&a?ss(ns(n.yaml,a.yaml)):[];return s`<div class="compare">
    <h3 class="block-title heading">Changes from ${K(he(e.a))} to ${K(he(e.b))}</h3>
    <pre class="diff code">${l.map(i=>i.kind==="skip"?s`<div class="diff-skip">⋯ ${i.count} unchanged lines</div>`:s`<div class=${`diff-${i.kind}`}>${i.kind==="added"?"+ ":i.kind==="removed"?"\u2212 ":"  "}${i.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${r?.title??e.a}</h3><${at} path=${e.path} view=${r} plain /></div>
      <div><h3 class="block-title heading">${o?.title??e.b}</h3><${at} path=${e.path} view=${o} plain /></div>
    </div>
  </div>`}function is(e){return E(()=>{document.title=`${e.path==="."?"local":e.path} \xB7 Beamtime`},[e.path]),e.history?s`<div class="page"><div class="sections">
      <${B} label=${ls(e.path)}><${yt} path=${e.path} /><//>
      <${B} label="history"><${os} path=${e.path} /><//>
    </div></div>`:s`<div class="page">
    <${Js} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function Js(e){let t=w(pe(e.path,e.version,e.draft));E(()=>{t.status==="ready"&&requestAnimationFrame(Pt)},[t.status==="ready"]);let n=s`
    <${B} label=${ls(e.path)}>
      <${yt} path=${e.path} finding=${t.data?.finding} />
      ${t.data?s`<${rs} path=${e.path} view=${t.data} />`:null}
    <//>
    ${le(e.path.split("/").pop()??"")?null:s`<${Gn} path=${e.path} />`}`;return t.status==="error"?s`<div class="sections">${n}
      <${B} label="view">
        ${Zs(e.path,t.error)?s`<${O} kind="warning">${t.error} The page fills in once the remote answers again.<//>`:s`<${O} kind="error">${t.error}<//>`}
      <//>
    </div>`:s`<${at} path=${e.path} view=${t.data} before=${n} />`}function ls(e){return le(e.split("/").pop()??"")?"run":"group"}function Zs(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function cs(e){E(()=>{xe(pe(e.id)).then(n=>D(x(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=w(pe(e.id));return t.status==="error"?s`<div class="page"><${O} kind="error">${t.error}<//></div>`:s`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var Qs={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},xt=20,Ne=-1,ea=[["day",86400],["week",7*86400],["month",30*86400]];function us(e){let t=L(w(oe()).data).map(i=>i.path),n=w({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),a=w({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});E(()=>{document.title="Timeline \xB7 Beamtime"},[]);let r=Date.now()/1e3,o=L(n.data).filter(i=>i["run.created_at"]).map((i,c)=>({id:i["run.id"],name:i["run.name"]??i["run.id"],group:i["run.group"],status:i["run.status"],start:Date.parse(i["run.created_at"])/1e3,end:i["run.ended_at"]?Date.parse(i["run.ended_at"])/1e3:r,lane:c})),l=(a.data?.entries??[]).map(i=>({id:i.id,type:i.type,group:i.group,description:i.description,t:Date.parse(he(i.id))/1e3}));return s`<div class="page timeline-page"><div class="sections">
    <${B} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${ze} label="Group" inline>
          <select value=${e.from} onChange=${i=>D(Ke(i.target.value),{replace:!0})}>
            ${t.map(i=>s`<option value=${i}>${i==="."?"everything":i}</option>`)}
          </select><//>
        <span class="muted small">${o.length} runs · ${l.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${B} label="runs">
      ${n.status==="error"?s`<${O} kind="error">${n.error}<//>`:null}
      ${n.data&&a.data?s`<${ta} bars=${o} marks=${l} />`:s`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function ta(e){let t=re(),n=H(null),a=[...e.bars.flatMap($=>[$.start,$.end]),...e.marks.map($=>$.t)],r=a.length?ds(Math.min(...a),Math.max(...a)):ds(Date.now()/1e3-86400,Date.now()/1e3),[o,l]=g(r),i=e.bars.length,c=Math.min(900,Math.max(160,(i+1.5)*xt+40)),d=rn(n,on,t?($=>{let k=tn(o[0],o[1]),m=h=>$.colors[Qs[h]??"muted"],f=h=>$.colors[h==="verdict"?"good":h==="decision"?"accent":h==="question"?"warn":"muted"];return{style:Ht($),height:c,x:{range:o,log:!1,format:h=>nn(h,k.step),splits:k.at},y:{range:[Ne-.8,i+.5],log:!1,reverse:!0,size:150,splits:i<=40?[Ne,...e.bars.map(h=>h.lane)]:[Ne],format:h=>h===Ne?"notes":oa(e.bars[Math.round(h)]?.name??"")},draw:({ctx:h,x:I,y:W,px:U,focused:P})=>{let G=xt*.62*U;for(let M of e.bars){let Q=I(M.start),fe=Math.max(3*U,I(M.end)-Q);h.fillStyle=P!==null&&P!==M.id?Bt(m(M.status),.35):m(M.status),h.beginPath(),h.roundRect(Q,W(M.lane)-G/2,fe,G,3*U),h.fill()}for(let M of e.marks){let Q=I(M.t),fe=W(Ne),z=(P===M.id?6:4.5)*U;h.fillStyle=f(M.type),h.beginPath(),h.moveTo(Q,fe-z),h.lineTo(Q+z,fe),h.lineTo(Q,fe+z),h.lineTo(Q-z,fe),h.closePath(),h.fill()}},hit:(h,I,W,U)=>{if(Math.abs(I-U(Ne))<xt/2){let M=ra(e.marks,Q=>Math.abs(W(Q.t)-h),8);return M?{key:M.id,rows:sa(M)}:null}let P=Math.round((I-U(0))/(U(1)-U(0))),G=e.bars.find(M=>M.lane===P&&W(M.start)-3<=h&&h<=Math.max(W(M.end),W(M.start)+3)+3);return G?{key:G.id,rows:na(G)}:null},onClick:h=>{let I=e.marks.find(W=>W.id===h);I?D(x(I.group,{drawer:!0})):D(ce(h))}}})(t):null,[o,e.bars,e.marks],t),p=$=>{if(!d.current)return;$.preventDefault();let k=d.current.xAt($.clientX),m=Math.exp($.deltaY*.0015);l(([f,h])=>St([k-(k-f)*m,k+(h-k)*m],r))},y=H(null),b=$=>y.current={x:$.clientX,range:o},T=$=>{if(!y.current||!d.current||!($.buttons&1))return;let k=($.clientX-y.current.x)*d.current.xPerPixel(),[m,f]=y.current.range;Math.abs($.clientX-y.current.x)>3&&l(St([m-k,f-k],r))},R=Math.max(...a,Date.now()/1e3);return s`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${ea.map(([$,k])=>s`<button type="button" role="radio" aria-checked=${Math.abs(o[1]-o[0]-k)<1}
          onClick=${()=>l(St([R-k,R+k*.02],[Math.min(r[0],R-k),r[1]]))}>last ${$}</button>`)}
      <button type="button" role="radio" aria-checked=${o[0]===r[0]&&o[1]===r[1]} onClick=${()=>l(r)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${c}px`}
      onWheel=${p} onPointerDown=${b} onPointerMove=${T} onPointerUp=${()=>y.current=null}></div>
    <p class="muted small">${aa(t)}</p>
  </div>`}function na(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:K(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:Ee(e.end-e.start),color:null}]}function sa(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:K(new Date(e.t*1e3).toISOString()),color:null}]}function aa(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function ra(e,t,n){let a=null,r=n;for(let o of e){let l=t(o);l<r&&([a,r]=[o,l])}return a}function ds(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function St([e,t],n){let a=Math.min(n[1]-n[0],Math.max(60,t-e)),r=Math.max(n[0],Math.min(e,n[1]-a));return[r,r+a]}function oa(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function ms(){let e=N(Oe),t=H(null);if(E(()=>{let r=t.current;if(!r||!e)return;r.showModal();let o=()=>Oe.set(null);return r.addEventListener("close",o),()=>r.removeEventListener("close",o)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},a=String(n.props.title??n.props.y??"Chart");return s`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${a} closedby="any">
    <${q.Provider} value=${e.view}><${se} node=${n} /><//>
  </dialog>`}function ps(e,t){let n=e.toLowerCase(),a=t.toLowerCase();if(!n)return 1;let r=a.indexOf(n);if(r>=0)return 100-Math.min(r,50)-a.length/100;let o=0,l=0;for(let i of a)if(i===n[o]?o++:o>0&&l++,o===n.length)return 40-Math.min(l,39);return 0}function fs(e){let[t,n]=g(e.query),[a,r]=g(0),o=H(null),l=L(w(oe()).data),i=L(w(tt()).data);E(()=>{let m=o.current;m.showModal();let f=()=>J.set(null);m.addEventListener("close",f);let h=!1,I=P=>{let G=m.getBoundingClientRect();return P.clientX<G.left||P.clientX>G.right||P.clientY<G.top||P.clientY>G.bottom},W=P=>h=I(P),U=P=>h&&I(P)&&m.close();return"closedBy"in HTMLDialogElement.prototype||(m.addEventListener("pointerdown",W),m.addEventListener("pointerup",U)),()=>{m.removeEventListener("close",f),m.removeEventListener("pointerdown",W),m.removeEventListener("pointerup",U)}},[]);let c=()=>o.current?.close(),u=m=>()=>D(m),d=V.value,p=d.page==="group"?d.path:".",y=(m,f,h,I)=>({section:"Commands",label:m,detail:f,sym:{icon:h,tone:"muted",label:m},run:I}),T=[...l.map(m=>({section:"Groups",label:m.path==="."?"local":m.path,detail:`${m.runs} runs${m.proposal?` \xB7 ${m.proposal}`:""}`,sym:C("research",m.status),run:u(x(m.path))})),...i.map(m=>({section:"Runs",label:m["run.name"]??m["run.id"],detail:`${m["run.status"]} \xB7 ${m["run.path"]}`,sym:C("run",m["run.status"]),run:u(x(m["run.path"]))})),y("Theme: light","","sun",()=>Fe("light")),y("Theme: dark","","moon",()=>Fe("dark")),y("Theme: follow the system","","monitor",()=>Fe("system")),y("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),y("Show notes and timeline","i","file-text",u(x(p,{drawer:!0}))),y("Show or hide the sidebar","\u2318B","panel-left",()=>Y.set(!Y.value)),y(ee.value?"Resume live updates":"Pause live updates","p",ee.value?"play":"pause",()=>ee.set(!ee.value)),y("Keyboard shortcuts","?","keyboard",()=>me.set(!0)),y("Settings","","settings",u("/settings/appearance"))].map(m=>({it:m,s:Math.max(ps(t,m.label),ps(t,m.detail)*.5)})).filter(m=>m.s>0).sort((m,f)=>f.s-m.s||$s(m.it.section)-$s(f.it.section)).slice(0,60).map(m=>m.it),R=m=>{m&&(c(),m.run())},$=m=>{if(m.key==="ArrowDown")r(Math.min(T.length-1,a+1));else if(m.key==="ArrowUp")r(Math.max(0,a-1));else if(m.key==="Enter")R(T[a]);else return;m.preventDefault()},k="";return s`<dialog class="sheet" ref=${o} aria-label="Search" closedby="any">
    <div class="palette-input"><${v} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${T[a]?`pal-${a}`:void 0}
        onInput=${m=>{n(m.target.value),r(0)}} onKeyDown=${$} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${T.map((m,f)=>{let h=m.section!==k&&!t?k=m.section:null;return s`${h?s`<li class="palette-head small" role="presentation">${h}</li>`:null}
          <li id=${`pal-${f}`} class="item" role="option" aria-selected=${f===a}
              onMouseMove=${()=>r(f)} onClick=${()=>R(m)}>
            <${_} spec=${m.sym} /><span class="label">${m.label}</span><span class="detail small">${m.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function $s(e){return["Groups","Runs","Commands"].indexOf(e)}function rt(e,t=[]){let n=new Map,a=(o,l={})=>({path:o,name:o==="."?"local":o.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let o of e)n.set(o.path,a(o.path,o));n.has(".")||n.set(".",a("."));for(let o of t)o.name!=="local"&&(n.has(o.name)||n.set(o.name,a(o.name)),Object.assign(n.get(o.name),{state:o.state,error:o.error}));for(let o of n.values()){if(F(o.path))continue;let l=o.path.lastIndexOf("/"),i=l<0?".":o.path.slice(0,l);(n.get(i)??n.get(be(o.path))??n.get(".")).children.push(o)}for(let o of n.values())o.children.sort((l,i)=>l.name.localeCompare(i.name));let r=[...n.values()].filter(o=>o.path!=="."&&F(o.path)).sort((o,l)=>o.name.localeCompare(l.name));return[n.get("."),...r]}function hs(e,t,n,a=new Set){let r=[],o=n.toLowerCase(),l=i=>{(!o||i.path.toLowerCase().includes(o)||gs(i,o))&&(r.push(i),(o||(F(i.path)?!a.has(i.path):t.has(i.path)))&&i.children.forEach(l))};return e.forEach(l),r}function gs(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||gs(n,t))}function vs(e,t){if(F(t))return e;let n=t.lastIndexOf("/"),a=n<0?".":t.slice(0,n),r=o=>o.path===a?o:o.children.map(r).find(l=>l)??null;return e.map(r).find(o=>o)?.children??[]}function bs(e){return F(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function ys(){let e=N(V),t=w(oe()),[n,a]=g(()=>new Set(we("open",[]))),[r,o]=g(()=>new Set(we("closed-hosts",[]))),[l,i]=g(""),c=H(null),u=e.page==="group"?e.path:null,d=rt(L(t.data),t.data?.meta?.sources??[]),p=hs(d,ca(n,u),l,r),y=$=>F($)?!r.has($):n.has($),b=($,k)=>{let m=k??!y($);if(F($)){let h=new Set(r);m?h.delete($):h.add($),ke("closed-hosts",[...h]),o(h);return}let f=new Set(n);m?f.add($):f.delete($),ke("open",[...f]),a(f)},T=H(u);return E(()=>{u!==T.current&&u&&!F(u)&&r.has(be(u))&&b(be(u),!0),T.current=u},[u]),s`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${v} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${l} aria-label="Filter groups"
        onInput=${$=>i($.target.value)} />
    </label>
    <div class="tree" ref=${c} onKeyDown=${$=>{let k=[...c.current?.querySelectorAll("a.tree-item")??[]],m=k.indexOf(document.activeElement),f=p[m];switch($.key){case"ArrowDown":k[Math.min(k.length-1,m+1)]?.focus();break;case"ArrowUp":k[Math.max(0,m-1)]?.focus();break;case"ArrowRight":f?.children.length&&b(f.path,!0);break;case"ArrowLeft":f?.children.length&&y(f.path)?b(f.path,!1):f&&k[p.findIndex(h=>h.path===la(f.path))]?.focus();break;default:return}$.preventDefault()}} role="tree">
      ${p.map($=>s`<${ia} key=${$.path} node=${$} current=${$.path===u}
        open=${y($.path)||!!l} onToggle=${()=>b($.path)} />`)}
    </div>
  </nav>`}function ia(e){let t=e.node,n=()=>He(t.path),a=t.children.length>0,r=t.state==="unreachable";return s`<a class=${`tree-item${e.current?" current":""}${t.path.startsWith("@")&&F(t.path)?" source-root":""}`} href=${x(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${a?e.open:void 0}
      style=${`padding-inline-start:${8+bs(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${o=>{o.metaKey||o.ctrlKey||(o.preventDefault(),D(x(t.path)))}}>
    <span class="twisty" onClick=${o=>{o.preventDefault(),o.stopPropagation(),e.onToggle()}}>
      ${a?s`<${v} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    ${F(t.path)?s`<${_} size=${14} spec=${{icon:r?"cloud-off":"server",tone:"muted",label:r?`Unreachable: ${t.error??"no answer"}`:t.path==="."?"This machine":`Remote host ${t.name}`}} />`:null}
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?s`<${_} spec=${C("run","running")} size=${14} />`:null}
      ${t.failed?s`<${_} spec=${{...C("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function la(e){if(F(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function ca(e,t){if(!t||t===".")return e;let n=new Set(e),a=t.split("/");for(let r=1;r<a.length;r++)n.add(a.slice(0,r).join("/"));return n}function ks(){let e=N(V),t=N(Y),n=N(J),a=N(me),r=H(null);E(()=>Rt(()=>r.current),[]),E(()=>(addEventListener("keydown",ws),()=>removeEventListener("keydown",ws)),[]);let o=e.page==="group"&&e.drawer,l;switch(e.page){case"group":l=s`<${is} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":l=s`<${cs} id=${e.id} />`;break;case"settings":l=s`<${En} />`;break;case"timeline":l=s`<${us} key=${e.from} from=${e.from} />`;break;default:l=s`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return de||!1?s`<main class="main render-main" ref=${r}>${l}</main>`:s`<div class=${`shell${t?"":" no-sidebar"}${o?" with-drawer":""}`}>
    <${Pn} />
    ${t?s`<${ys} />`:null}
    <main class="main" ref=${r}>${l}</main>
    ${o?s`<${Wn} path=${e.path} run=${e.run} />`:null}
    <${On} />
    ${n!==null?s`<${fs} query=${n} />`:null}
    ${a?s`<${ua} />`:null}
    <${ms} />
  </div>`}function ws(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),J.set(J.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),Y.set(!Y.value);return}if(e.key==="Escape"){if(J.value!==null||me.value)return;let a=V.value;return a.page==="group"&&a.run?D(x(a.path,{drawer:!0}),{replace:!0}):a.page==="group"&&a.drawer?D(x(a.path),{replace:!0}):void 0}if(t||e.altKey||xn(e)||J.value!==null||me.value)return;let n=V.value;switch(e.key){case"/":e.preventDefault(),J.set("");break;case"?":me.set(!me.value);break;case"p":ee.set(!ee.value);break;case"i":n.page==="group"&&D(x(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":Y.set(!Y.value);break;case"[":case"]":n.page==="group"&&da(n.path,e.key==="]"?1:-1);break}}async function da(e,t){let n=await xe(oe()),a=vs(rt(L(n),n?.meta?.sources??[]),e),r=a.findIndex(l=>l.path===e),o=a[r+t];o&&D(x(o.path))}function ua(){let e=H(null);return E(()=>{let t=e.current;t.showModal();let n=()=>me.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),s`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${Ye.map(([t,n])=>s`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${ne} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}Ot();if(de){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(ue.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Le.n,It&&Ft()}$n();var ma=A("meta").then(e=>(de&&(e={...e,settings:{...e.settings,theme_mode:ue.value}}),Je(e),e));!de&&!!1&&Lt(async()=>{let[e,t]=await Promise.all([ma,A("meta")]);e.bundle!==t.bundle?location.reload():Je(t)});Et(s`<${ks} />`,document.getElementById("app"));
