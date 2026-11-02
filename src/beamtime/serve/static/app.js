import{$ as re,$a as cn,A as _t,B as Lt,C as we,Ca as Ge,D as le,Da as M,E as k,Ea as ut,F as Ae,Fa as Gt,G as ce,Ga as mt,H as Le,Ha as Ve,I as Ke,Ia as qe,J,Ja as Vt,K as G,Ka as qt,L as Rt,La as Xt,Ma as Yt,N as _,Na as Jt,O as Pt,P as Ot,Q as de,Qa as Zt,R as Re,Ra as Qt,S as It,Sa as en,T as Ue,Ta as tn,U as it,Ua as nn,V as ue,Va as sn,W as At,Wa as an,X as lt,Xa as rn,Y as Fe,Z as V,Za as on,_ as ae,_a as ln,aa as je,ab as dn,ba as Kt,bb as un,c as Et,ca as Pe,cb as mn,d as s,da as Oe,db as pn,e as h,eb as $n,f as T,fa as Ut,g as Ct,ga as Ft,h as H,ha as v,i as Me,ia as L,j as ie,ja as We,ka as te,la as O,m as ve,ma as R,n as D,na as ct,o as Ne,oa as F,p as De,pa as jt,qa as B,ra as ne,s as A,sa as Ie,t as _e,ta as dt,u as ye,ua as Wt,v as ot,va as q,w as y,wa as he,x as Nt,xa as be,y as ee,ya as ke,z as Dt,za as K}from"./chunks/chunk-NUKRIPYV.js";import{a as Tt,b as Mt}from"./chunks/chunk-O2K4N3UR.js";import{e as zt,i as Bt,j as Ht}from"./chunks/chunk-CHIPVRI3.js";import"./chunks/chunk-VC46IEJQ.js";function xe(e,t){we(n=>t.includes(n.method)&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var pt=["notes","timeline","groups","check","card","memory_show","status"];async function $t(e,t){let n=e.meta??{};await A("note_add",{group:e.group,type:e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),xe(e.group,pt)}async function fn(e,t,n,a){await A("note_add",{group:e,type:t,description:n,body:a}),xe(e,pt)}async function hn(e,t){await A("memory_update",{group:e,body:t}),xe(e,["memory_show","status"])}async function gn(e,t){let n=await A("proposal_show",{group:e}),a=Object.fromEntries(Object.entries(n.proposal??{}).filter(([r])=>!["schema","author","user","supersedes"].includes(r)));await A("proposal_set",{group:e,proposal:{...a,statement:t}}),xe(e,["groups","proposal_show","check","summary"])}async function vn(e){await A("note_rm",{note:e.id}),xe(e.group,pt)}async function bn(e,t,n){await A("name",{run:e,name:n}),xe(t,["card","runs","groups","summary","series"])}async function Xe(e,t,n){let a=await A("view_text",{path:e,id:t,text:n});return we(r=>["view","view_history"].includes(r.method)&&r.scope===e),a.id}async function yn(e){await A("view_upgrade",{group:e}),we(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var Se=new ve(null);async function wn(e,t){return await A("set",{key:e,value:t}),A("meta")}var X=new ve(Ne("sidebar",!0)),Y=new ve(null),me=new ve(!1),Ee=new ve(null);X.subscribe(e=>De("sidebar",e));var kn=Ne("visit",Date.now());De("visit",Date.now());function xn(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var Ye=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var ks=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function Je(e){Ee.set(e),Ue.set(e.theme),e.settings?.theme_mode&&ue.set(e.settings.theme_mode),lt()}async function ft(e,t){e==="theme_mode"&&(ue.set(t),lt()),Je(await wn(e,t))}function Sn(){let e=D(ue),t=re(),n=D(Ee),[a,r]=h(null);T(()=>{document.title="Settings \xB7 Beamtime"},[]);let o=(c,u)=>{r(null),ft(c,u).catch(d=>r(d.message))},l=n?.settings??{},i=(c,u,d)=>s`
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
          ${ks.map(([c,u,d])=>s`<button type="button" role="radio" aria-checked=${e===c} onClick=${()=>o("theme_mode",c)}>
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
  </div></div>`}var oe=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),pe=(e,t=null,n=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{}},scope:e}),ht=e=>({method:"summary",params:{path:e},scope:e}),Ze=e=>({method:"groups",params:{from:e,depth:0},scope:e}),En=e=>({method:"check",params:{group:e},scope:e}),Cn=e=>({method:"proposal_show",params:{group:e},scope:e}),Qe=(e,t)=>({method:"card",params:{run:Le(e,t)},scope:t}),Tn=(e,t)=>({method:"output",params:{run:Le(e,t),tail:30},scope:t}),ze=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),et=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),Mn=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),Nn=()=>({method:"status",params:{},scope:"."}),tt=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function Be(e){for(let t of[pe(e),Ze(e),ze(e),ht(e)])ot(t);ye(pe(e)).then(t=>{for(let n of Dn(t.view))ot(n)}).catch(()=>{})}function Dn(e){return e?[...xs.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(Dn)]:[]}var xs=new Set(["line","custom"]),_n=e=>({method:"view_history",params:{group:e},scope:e});var Ln={system:"light",light:"dark",dark:"system"},Ss={system:"monitor",light:"sun",dark:"moon"};function Rn(){let e=D(Ee),t=D(ue),n=D(X);return s`<header class="topbar">
    <${F} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>X.set(!n)} />
    <a class="project heading" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>Y.set("")} aria-label="Search (⌘K)">
      <${v} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${Es} />
      <${F} icon=${Ss[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${Ln[t]})`}
        onClick=${()=>{ft("theme_mode",Ln[t])}} />
      <a class="icon-button" href=${Ae(G.value.page==="group"?G.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${v} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${v} name="settings" size=${16} /></a>
    </div>
  </header>`}function Es(){let t=(y(oe()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?s`${[{name:"local",state:"connected"},...t].map(n=>s`<a class=${`source small ${n.state}`}
      href=${k(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${v} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:s`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${v} name="server" size=${15} /> local</span>`}function Cs(e){let[t,n]=h(Date.now());return T(()=>{let a=setInterval(()=>n(Date.now()),e);return()=>clearInterval(a)},[e]),t}function Ts(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function Pn(){let e=D(Dt),t=D(ee),n=D(_t),a=D(G),r=Cs(5e3),o=y(Nn()).data,l=R(y(tt()).data),i=D(Ee),c=o?.daemon,u=o?.runs?.running??0,d=l.filter(C=>C["run.status"]==="failed"&&Ts(C["run.ended_at"])>kn).length,p=o?.meta?.freshness,[$,f,S]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&c?["",`live \xB7 updated ${K(new Date(n).toISOString(),r)}`,`beamtime serve, pid ${c.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return s`<footer class="statusbar small">
    <span class="status-item" data-tip=${S}><span class=${`live-dot ${$}`}></span>${f}</span>
    ${u?s`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>Y.set("running")}>
          <${v} name="circle-dot" size=${14} class="tone-accent" />${u} running</button>`:null}
    ${d?s`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>Y.set("failed")}>
          <${v} name="circle-x" size=${14} />${d} failed since your last visit</button>`:null}
    ${p?.behind?s`<span class="status-item warn-text" data-tip=${p.text}><${v} name="hourglass" size=${14} />${p.behind} runs behind</span>`:null}
    ${p?.damaged?.length?s`<span class="status-item warn-text" data-tip=${p.damaged.join(`
`)}><${v} name="triangle-alert" size=${14} />${p.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${a.page==="group"&&a.run?s`<span class="status-item"><${v} name="activity" size=${14} />1 run selected</span>`:null}
    <${F} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>ee.set(!t)} />
    ${i?.outdated?s`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item">${i?.version?`beamtime ${i.version}`:""}</span>
  </footer>`}var On=null;function nt(e){let t=H(null),[n,a]=h(null),[r,o]=h(!1),[l,i]=h(!1);T(()=>{let p=!0;return On??=import("./chunks/md-SW3VT2BQ.js"),On.then($=>$.render(e.text??"")).then($=>p&&a($)),()=>{p=!1}},[e.text]),Ct(()=>{let p=t.current;if(!p||!e.clamp)return;let $=()=>i(p.scrollHeight>p.clientHeight+2),f=new ResizeObserver($);return f.observe(p),()=>f.disconnect()},[e.clamp,n]);let c=e.clamp&&!r,u=`md${c?" clamped":""}`,d=c?`--clamp:${e.clamp}`:"";return s`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?s`<div class=${u} ref=${t} style=${d}>
          ${(e.text??"").split(/\n{2,}/).map(p=>s`<p>${p}</p>`)}
        </div>`:s`<div class=${u} ref=${t} style=${d} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(l||r)?s`<button type="button" class="link small more" onClick=${()=>o(!r)}>${r?"less":"more"}</button>`:null}
  </div>`}function ge(e){let[t,n]=h(!!e.startEditing),[a,r]=h(e.value),[o,l]=h(null),[i,c]=h(null),u=H(null),d=H(!1);T(()=>l(null),[e.value]),T(()=>{!t||!u.current||(u.current.focus(),e.startEditing?u.current.select():u.current.setSelectionRange(u.current.value.length,u.current.value.length))},[t]);let[p,$]=h(!1),f=e.locked??void 0,S=b=>{if(!b.target.closest("a, button, input, summary")){if(f)return $(!0);b.preventDefault(),r(o??e.value),c(null),d.current=!1,n(!0)}},C=()=>{d.current=!0,n(!1),c(null),e.onCancel?.()},w=async()=>{if(d.current)return;d.current=!0;let b=e.multiline?a.trim():a.replace(/\s*\n\s*/g," ").trim();if(b===e.value.trim()||!b&&!e.multiline)return C();n(!1),l(b);try{await e.onSave(b)}catch(g){l(null),r(b),c(g.message),d.current=!1,n(!0)}},E=b=>{if(b.key==="Escape")return b.preventDefault(),b.stopPropagation(),C();b.key!=="Enter"||b.isComposing||b.keyCode===229||(!e.multiline||b.metaKey||b.ctrlKey)&&(b.preventDefault(),w())};if(t)return s`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${u} class="edit-field" value=${a} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,a.split(`
`).length+1)):1}
        onInput=${b=>r(b.target.value)} onKeyDown=${E} onBlur=${w}></textarea>
      <span class="edit-hint small">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${i?s` · <span class="bad-text">${i}</span>`:null}</span>
    </div>`;let m=o??e.value;return s`<div class=${`editable${f?" locked":""}${o!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${f?`${e.label}: ${f}`:`Edit ${e.label}`}
      data-tip=${f} onClick=${S} onBlur=${()=>$(!1)}
      onKeyDown=${b=>b.key==="Enter"&&b.target===b.currentTarget&&S(b)}>
    ${m.trim()?e.render?e.render(m):m:s`<span class="muted">${e.placeholder??"Click to write"}</span>`}
    ${p&&f?s`<span class="edit-hint small locked-why" role="status"><${v} name="lock" size=${14} /> ${f}</span>`:null}
  </div>`}function gt(e){let t=[];if(e.effect!==void 0&&e.effect!==null){let n=e.ci?` [${q(e.ci[0])}, ${q(e.ci[1])}]`:"";t.push(`${e.effect>=0?"+":""}${q(e.effect)}${n}`)}return e.threshold!==void 0&&e.threshold!==null&&t.push(`needs ${e.op} ${q(e.threshold)}`),e.points&&t.push(`${e.points} point${e.points>1?"s":""}`),e.detail&&t.push(e.detail),t.join(" \xB7 ")}function vt(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function In({node:e}){let t=ae("proposal"),n=ae("check"),a=t.data,r=n.data;if(!a)return s`<${te} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let o=a.proposal??{},l=(a.versions??[]).filter(c=>c.version!==a.version),i=!e.props.of||e.props.of===".";return s`<${te} title="Predictions" result=${t} class="proposal">
    ${i?null:s`<p class="statement">${o.statement}</p>`}
    ${o.rationale?s`<p class="rationale prose">${o.rationale}</p>`:null}
    <div class="predictions">
      ${(r?.predictions??[]).map(c=>s`<div class="prediction" key=${c.name}>
          <${L} spec=${M("result",c.result)} />
          <span class="pname">${c.name}</span>
          <span class="pdetail num small">${gt(c)}</span>
        </div>`)}
    </div>
    ${l.length?s`<${dt} summary=${`${l.length} earlier version${l.length>1?"s":""}`}>
          ${l.map(c=>s`<p class="small"><code>${c.version}</code> ${c.statement}
            <span class="muted">(${c.runs} runs, check ${c.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function zn({node:e}){let t=ae("main"),n=e.data?.main.params.group??".",a=t.data?.chain??[],r=a.find(i=>i.group===n)??null,o=a.filter(i=>i.group!==n),l=r?.notes_since?"out of date":r?`version ${r.versions??1}`:"none yet";return s`<${ct} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?l:void 0} open=${!1} result=${t}
      action=${s`<${L} spec=${{icon:"circle-help",tone:"muted",label:Ns}} />`}>
    <${ge} value=${r?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${i=>s`<${nt} text=${i} />`} onSave=${i=>hn(n,i)} />
    ${r&&(r.body?.length>(t.data?.budget??1/0)||r.notes_since>=Ms)?s`<p class="memory-meta small warn-text">${r.body?.length>t.data.budget?`${r.body.length} characters, beyond the budget of ${t.data.budget}`:`${r.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${r?s`<p class="memory-meta small">${r.author} · covers notes until ${r.covers_until?.slice(0,10)}
          ${r.notes_since?s` · <span class="warn-text">${r.notes_since} newer note${r.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${o.length?s`<p class="memory-meta small">Memory above this group: ${o.map((i,c)=>s`${c?", ":""}<a href=${k(i.group)}>${i.group==="."?"local":i.group}</a>`)}</p>`:null}
  <//>`}var Ms=5,Ns="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",Ds="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function Bn({node:e}){let t=ae("main"),n=e.data?.main.params.from??".",a=R(t.data).filter(r=>r.path!==n);return s`<${te} title=${e.props.title} count=${t.data?String(a.length):void 0} result=${t}>
    ${t.data&&!a.length?s`<${O}>No groups below.<//>`:null}
    <div class="group-list">
      ${a.map(r=>{let[o,l]=vt(r.progress),i=(r.failed??0)+(r.killed??0)+(r.lost??0);return s`<a class="group-row" key=${r.path} href=${k(r.path)}
            onPointerEnter=${()=>Be(r.path)} onFocus=${()=>Be(r.path)}>
          <${L} spec=${M("research",r.status)} />
          <span class="gname heading">${r.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${r.status!=="concluded"?s`<span class=${`tone-${M("research",r.status).tone}`}>${M("research",r.status).label}</span>`:null}
            ${r.check?s`<${L} spec=${M("result",r.check)} word />`:null}
            ${r.verdict?s`<${L} spec=${M("verdict",r.verdict)} />`:null}
            ${o?s`<span data-tip=${l}>${o}</span>`:null}
            <span class="num"><b>${r.runs}</b> runs</span>
            ${r.running?s`<${L} spec=${M("run","running")} />`:null}
            ${i?s`<span class="tone-bad num" data-tip="failed, killed or lost"><${v} name="circle-x" size=${14} /> ${i}</span>`:null}
          </span>
          ${r.proposal?s`<span class="gstatement caption">${r.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function Hn({node:e}){let t=ae("main"),n=e.data?.main.params.from??".",[a,r]=h(!1),o=(t.data?.entries??[]).filter(i=>!String(i.state??"").startsWith("superseded")),l=t.data?.meta?.matched??o.length;return s`<${ct} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(l):void 0} result=${t}
      action=${s`<${L} spec=${{icon:"circle-help",tone:"muted",label:Ds}} />
        ${s`<${F} icon="plus" label="Add a note" onClick=${()=>r(!0)} />`}`}>
    <div class="notes">
      ${a?s`<${Rs} group=${n} onDone=${()=>r(!1)} />`:null}
      ${t.data&&!o.length&&!a?s`<p class="muted small">No notes yet.</p>`:null}
      ${o.map(i=>s`<${st} key=${i.id} note=${i} scope=${n} />`)}
      ${t.data?.more&&e.data?s`<${An} call=${e.data.main} before=${o[o.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var _s=20;function An(e){let[t,n]=h(!1),a=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:_s}}:null,r=y(a);if(!t)return s`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(r.status==="error")return s`<p class="bad-text small">${r.error}</p>`;let o=r.data?.entries??[];return s`${r.data?null:s`<div class="skeleton" style="block-size: 40px"></div>`}
    ${o.map(l=>s`<${st} key=${l.id} note=${l} scope=${e.scope} />`)}
    ${r.data?.more?s`<${An} call=${e.call} before=${o[o.length-1]?.id} scope=${e.scope} />`:null}`}var Ls=["observation","idea","question","decision"];function Rs(e){let[t,n]=h("observation"),[a,r]=h(""),[o,l]=h(""),[i,c]=h(null),[u,d]=h(!1),p=async f=>{if(f.preventDefault(),!a.trim())return c("give the note a title");d(!0);try{await fn(e.group,t,a.trim(),o.trim()),e.onDone()}catch(S){c(S.message),d(!1)}};return s`<form class="note new-note" onSubmit=${p} onKeyDown=${f=>{f.key==="Escape"&&e.onDone(),f.key==="Enter"&&(f.metaKey||f.ctrlKey)&&p(f)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${t} aria-label="Note type" onChange=${f=>n(f.target.value)}>
        ${Ls.map(f=>s`<option value=${f}>${f}</option>`)}
      </select></span>
      <span class="input body new-note-field"><input class="new-note-title" value=${a} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${f=>r(f.target.value)} /></span>
    </div>
    <span class="input small"><textarea class="new-note-body" rows="4" value=${o} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${f=>l(f.target.value)}></textarea></span>
    <div class="save-actions">
      <${ne} type="submit" icon=${u?"hourglass":"plus"} disabled=${u}>${u?"Adding\u2026":"Add note"}<//>
      <${ne} icon="x" kind="quiet" onClick=${e.onDone}>Cancel<//>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${i?s`<span class="bad-text small">${i}</span>`:null}
    </div>
  </form>`}function st(e){let t=e.note,[n,a]=h(!!e.open),[r,o]=h(!1),l=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,i=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),c=t.meta?.author;return s`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${u=>!u.target.closest(".editable, a, .note-delete")&&a(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${v} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${L} spec=${M("note",t.type)} />
      <${ge} value=${t.description} label="the note's title" class="note-title heading" render=${Os}
        onSave=${u=>$t(t,{description:u})} />
      ${t.overall?s`<${L} spec=${M("verdict",t.overall)} />`:null}
      ${t.state?s`<${jt} tone="warn">${t.state}<//>`:null}
      ${l?s`<a class="note-group small" href=${k(l)} data-tip="from this group">${Ps(l,e.scope)}</a>`:null}
      <span class="note-meta small">${c?`${c} \xB7 `:""}${K(i)}</span>
      ${s`<${F} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${r}
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
  </article>`}function Ps(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,a=n.split("/").pop()??n;return le(a)?a.slice(-8):n}function Kn({node:e}){let t=ae("main"),n=t.data?.lines??[],a=t.data?.meta??{},r=s`<${v} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${a.total_lines??n.length} lines${(a.shown??0)<(a.total_lines??0)?`, last ${a.shown}`:""}`:""}</span>`;return s`<${te} result=${t}>
    <${dt} summary=${r} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function Un({node:e}){let t=ie(V);return s`<${te} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${ge} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${Se.value===e.id} onCancel=${()=>Se.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>s`<${nt} text=${n} />`}
      onSave=${n=>(Se.set(null),Xe(t.path,e.id,n))} />
  <//>`}function Fn({node:e}){return s`<${O} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function Os(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let a=n.slice(2,-2),[r]=a.split(/[#@]/),o=r.split("/").pop()??"";return s`<a href=${le(o)?ce(o):k(r)}>${a}</a>`}return n.startsWith("`")?s`<code>${n.slice(1,-1)}</code>`:n})}function jn(e){let t=()=>_(k(e.path),{replace:!0});return s`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${v} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${F} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?s`<${Is} id=${e.run} scope=${e.path} />`:s`<${zs} path=${e.path} />`}
  </aside>`}function Is({id:e,scope:t}){let n=y(Qe(e,t)).data,a=y(Tn(e,t)).data,r=y(ze(t)).data,o=re(),l=Me(()=>je(R(r).map(d=>d["run.id"]),o).get(e),[r,o,e]);if(!n)return s`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let i=n.run,c=Object.entries(n.metrics??{}),u=zt(l,o);return s`<div class="drawer-body">
    <h3 class="heading"><span class=${u.class} style=${u.style}></span>
      <a href=${ce(e)}>${i.name}</a></h3>
    <p class="facts small">
      <${L} spec=${M("run",i.status)} word />
      <span><b>${be(i.steps)}</b> steps</span>
      <span><b>${ke(i.duration_s)}</b></span>
      <span data-tip=${i.created_at}>${K(i.created_at)}</span>
    </p>
    ${i.error?s`<pre class="log code bad-text">${i.error}</pre>`:null}
    <h4 class="small">Config</h4>
    <table class="kv small">${Object.entries(n.config??{}).map(([d,p])=>s`<tr><td>${d}</td><td class="num">${q(p)}</td></tr>`)}</table>
    ${c.length?s`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${c.map(([d,p])=>s`<tr><td>${d}</td><td class="num"><b>${q(p.last)}</b></td>
              <td class="num">${q(p.min)}</td><td class="num">${q(p.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?s`<h4 class="small">Cited by</h4>${n.cited_by.map(d=>s`<p class="small"><${L} spec=${M("note",d.type)} /> ${d.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(d=>s`<div class="event small"><span class="muted num">${d.t?.slice(5,16).replace("T"," ")}</span>
        <${v} name=${ut(d.type)} size=${14} /><span>${d.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(a?.lines??[]).join(`
`)}</pre>
  </div>`}function zs({path:e}){let t=y(et(e)).data,n=y(Mn(e)).data;return s`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?s`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(a=>!String(a.state??"").startsWith("superseded")).map(a=>s`<${st} key=${a.id} note=${a} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(a=>s`<div class="event small"><span class="muted num">${a.t?.slice(5,16).replace("T"," ")}</span>
        <${v} name=${a.kind==="note"?"file-text":ut(a.type)} size=${14} />
        <span>${a.run?s`<a href=${ce(a.run)}>${a.run.slice(-8)}</a> `:null}${a.description??a.type}</span></div>`)}
  </div>`}var bt=["failed","killed","lost"];function yt(e){let t=Ke(e.path),n=t==="."?e.path:e.path.slice(t.length+1),a=J(e.path)?[]:n.split("/"),r=a.length&&le(a[a.length-1])?a[a.length-1]:null,o=a.slice(0,-1),l=i=>[...t==="."?[]:[t],...o.slice(0,i+1)].join("/");return s`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${a.length?s`<a href=${k(t)}>${t==="."?"local":t}</a>`:null}
      ${o.map((i,c)=>s`<span>/</span><a href=${k(l(c))}>${i}</a>`)}
    </nav>
    ${r?s`<${As} id=${r} scope=${e.path} />`:s`<${Bs} path=${e.path} />`}
    ${e.finding?s`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function Bs({path:e}){let t=R(y(Ze(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return s`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=bt.reduce((r,o)=>r+(t[o]??0),0);return s`
    <h1 class="page-title title" tabindex="-1">${n} <${L} spec=${M("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?s`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?s`<span><b>${t.finished}</b> finished</span>`:null}
      ${a?s`<span class="tone-bad" data-tip=${bt.filter(r=>t[r]).map(r=>`${t[r]} ${r}`).join(", ")}>
            <${v} name="circle-x" size=${15} /> <b>${a}</b> ${a===1?bt.find(r=>t[r]):"ended early"}</span>`:null}
      ${t.notes?s`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${Gn} path=${e} />
    </p>`}function Wn({path:e}){let t=R(y(Ze(e)).data)[0]??null,n=y(t?.proposal?En(e):null).data,a=y(t?.proposal?Cn(e):null).data;if(!t?.proposal)return null;let r=a?.proposal?.rationale,o=a?.versions?.find(c=>c.version===a.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[l,i]=vt(n?.progress?.text??t.progress);return s`<${B} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${ge} value=${t.proposal} label="the proposal's statement" locked=${a?o:"Loading the proposal\u2026"}
          render=${c=>s`<span data-tip=${o?void 0:r}>${c}</span>`}
          onSave=${c=>gn(e,c)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(c=>{let u=M("result",c.result),d=gt(c),p=d?`${u.label}: ${d}`:u.label;return s`<span class=${`check small tone-${u.tone}`} key=${c.name} data-tip=${p}
              aria-label=${`${c.name}: ${p}`} tabindex="0"><${v} name=${u.icon} size=${14} />${c.name}</span>`})}
        ${n?.provisional||l?s`<span class="small">
              ${n?.provisional?s`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${l?s`<span class="muted" data-tip=${i}>${n?.provisional?" \xB7 ":""}${l}</span>`:null}
            </span>`:null}
      </div>
      <${Hs} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function Hs(e){let t=y(e.verdict?et(e.path):null).data;if(!e.verdict)return s`<p class="verdict-line muted">no verdict yet</p>`;let n=M("verdict",e.verdict),a=(t?.entries??[]).find(o=>o.type==="verdict"&&(o.group??e.path)===e.path),r=a?he(a.id):null;return s`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${v} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${a?s`<span class="small muted" data-tip=${r}>verdict${a.meta?.author?` by ${a.meta.author}`:""}${r?` \xB7 ${K(r)}`:""}</span>`:null}
  </p>`}function As({id:e,scope:t}){let n=y(Qe(e,t)).data;if(!n)return s`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=n.run,r=()=>{navigator.clipboard?.writeText(a.id)};return s`
    <h1 class="page-title title" tabindex="-1"><${ge} value=${a.name??a.id} label="the run's name" class="title-edit"
        onSave=${o=>bn(a.id,t,o.trim())} />
      <${L} spec=${M("run",a.status)} word /></h1>
    ${a.error?s`<p class="bad-text" data-tip=${a.error}>${a.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${be(a.steps)}</b> steps</span>
      <span><b>${ke(a.duration_s)}</b></span>
      <span data-tip=${a.created_at}>${K(a.created_at)}</span>
      <${Gn} path=${t} />
      <${F} icon="copy" label=${`Copy the run id ${a.id}`} onClick=${r} />
      <${Wt} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${Ks(a).map(([o,l])=>s`<tr><td class="muted">${o}</td><td>${l}</td></tr>`)}</table>
        <div class="menu-list">
          <button type="button" onClick=${()=>_(k(t,{run:a.id}),{replace:!0})}>
            <${v} name="panel-right" size=${15} /> Open in the side panel</button>
          <button type="button" onClick=${r}><${v} name="copy" size=${15} /> Copy the run id</button>
          ${a.git?.commit?s`<button type="button" onClick=${()=>navigator.clipboard?.writeText(a.git.commit)}>
            <${v} name="git-commit" size=${15} /> Copy the commit</button>`:null}
        </div>
      <//>
    </div>
    ${(n.proposals??[]).length?s`<div class="checks">
          ${n.proposals.map(o=>{let l=M("result",o.check);return s`<a class=${`check small tone-${l.tone}`} href=${k(o.group)} data-tip=${o.statement}>
              <${v} name=${l.icon} size=${14} />${o.group==="."?"own proposal":o.group}
              ${o.verdict?s`<${L} spec=${M("verdict",o.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function Gn({path:e}){let t=y(ht(e)).data?.summary;if(!t)return null;let n=Object.entries(t.config??{}).map(([r,o])=>`${r} ${q(o)}`).join(", "),a=le(e.split("/").pop()??"");return s`<span data-tip=${`${t.stat} of ${t.metric} over ${a?"the run":"all runs"}`}>
    best <b>${t.metric} ${q(t.value)}</b>
    ${a?null:s` · <a href=${ce(t.run)}>${t.name}</a>${n?s` <em>(${n})</em>`:null}`}
  </span>`}function Ks(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,a])=>[n,String(a)])}var Vn=15e3;function qn({node:e}){let t=ie(V),n=re(),[a,r]=Kt(),o=e.props.code,l=y(r&&o?{method:"code",params:o,scope:t.path}:null),[i,c]=h(null),[u,d]=h(120),[p,$]=h({error:null,warnings:[]}),f=w=>{de&&console.error(`[block ${e.id}] ${w}`),$(E=>({...E,error:w}))};T(()=>{let w=i?.contentWindow;if(!w||l.status!=="ready")return;let E=z=>w.postMessage(z,"*"),m=new Map,b=new en,g=!0;_e.n++;let I=()=>{g&&_e.n--,g=!1},j=setTimeout(()=>{g&&f(`no first render within ${Vn/1e3} s`),I()},Vn),U=z=>{if(z.source!==w)return;let x=z.data;switch(x.type){case"hello":E({type:"init",init:{id:e.id,code:l.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:At.value,pair:Ue.value,prefs:mt(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics}});break;case"sub":if(!Jt.has(x.call.method)){E({type:"result",id:x.id,result:{status:"error",data:null,error:`${x.call.method} is not available in a custom block`,refreshing:!1}});break}m.get(x.id)?.(),m.set(x.id,Nt(x.call,Te=>E({type:"result",id:x.id,result:Te})));break;case"unsub":m.get(x.id)?.(),m.delete(x.id);break;case"navigate":x.url.startsWith("/")&&_(x.url);break;case"height":b.accept(performance.now())?d(Math.max(40,x.height)):P("its height keeps changing, so it is fixed at its last height");break;case"ready":$(Te=>({...Te,blank:x.blank,overflow:x.overflow})),I();break;case"warn":P(x.message);break;case"hover":it.set(x.run);break;case"prefs":JSON.stringify(N.value)!==JSON.stringify(x.prefs)&&N.set(x.prefs);break;case"download":case"snapshot":x.href?Zt(x.href,x.name)?performance.now()-W>1e3&&(W=performance.now(),Oe().download(x.href,x.name)):P(`a download of ${x.name} was refused: only PNG, SVG and CSV files`):P("it draws no SVG or canvas to download");break;case"figure":Oe().figure(x.spec,x.name).catch(Te=>P(`the PDF failed: ${Te.message}`));break;case"expand":Qt(x.node)&&Oe().expand(x.node,t);break;case"error":f(x.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,S)),I();break;default:break}},P=z=>{de&&console.warn(`[block ${e.id}] ${z}`),$(x=>x.warnings.includes(z)?x:{...x,warnings:[...x.warnings,z]})},W=-1/0,N=mt(t.path),Q=it.subscribe(z=>E({type:"hover",run:z})),fe=N.subscribe(z=>E({type:"prefs",prefs:z}));return addEventListener("message",U),E({type:"ping"}),()=>{Q(),fe(),removeEventListener("message",U),clearTimeout(j);for(let z of m.values())z();I()}},[l.status,l.data,i]),T(()=>{let w={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};i?.contentWindow?.postMessage(w,"*")},[t.names,t.colors,t.metrics,i]),T(()=>{n&&i?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let S=typeof o=="object"?o.path??o.block:String(o??"");Ut(e.id,{png:()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")});let C=r&&l.status==="ready"&&!p.error;return s`<div ref=${a} class="custom-block">
    <div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${C?s`<span class="chart-tools">
            <${F} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?s`<${F} icon="x" label="Close (Esc)" onClick=${()=>Pe.set(null)} />`:s`<${F} icon="maximize" label="Expand" onClick=${()=>Oe().expand(e,t)} />`}
          </span>`:null}
    </div>
    <${te} caption=${e.props.expanded?void 0:e.props.caption} result=${l}>
      ${p.error?s`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${S})</span>
            <pre class="code">${p.error}</pre>
          </div>`:null}
      ${p.warnings.map(w=>s`<${O} kind="warning">${w}<//>`)}
      ${C?s`<div class="custom-frame" data-frame-blank=${p.blank?"1":void 0} data-frame-overflow=${p.overflow?"1":void 0}>
            <iframe key=${l.data.code} ref=${c} sandbox="allow-scripts" ...${Us()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${u}px`} />
          </div>`:null}
    <//>
  </div>`}function Us(){if(!!1)return{src:Tt("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1").replace(/@font-face\s*\{[^}]*\}/g,""),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}function Xn({node:e}){let t=ae("main"),n=ie(V),a=t.data?.entries??[];return s`<${te} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!a.length?s`<${O}>No images logged.<//>`:null}
    <div class="images">
      ${a.map(r=>s`<figure key=${`${r.run}/${r.path}`}>
          <img src=${Mt(Le(r.run,n.path),r.path)} alt=${r.caption??e.props.title} loading=${Re?"eager":"lazy"} />
          <figcaption class="small">step ${be(r.step)}${r.caption?` \xB7 ${r.caption}`:""}</figcaption>
        </figure>`)}
    </div>
  <//>`}function Yn({node:e}){let t=ae("main"),n=t.data?.entries??[];return s`<${te} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?s`<${O}>No text logged.<//>`:null}
    ${n.map(a=>s`<div class="text-entry" key=${`${a.run}/${a.step}`}>
        <div class="muted small">step ${be(a.step)}${a.caption?` \xB7 ${a.caption}`:""}</div>
        <pre class="code">${a.text??""}</pre>
      </div>`)}
  <//>`}function Jn({node:e}){let[t,n]=h(Re||e.props.open!==!1),a=s`${(e.children??[]).map(l=>s`<${se} key=${l.id} node=${l} />`)}`,r=ie(We);if(!e.props.title)return s`<div class="stack">${a}</div>`;let o=r===e.props.title.toLowerCase();return s`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${t} aria-label=${o?`${t?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${()=>n(!t)}>
      <${v} name=${t?"chevron-down":"chevron-right"} size=${16} />${o?null:e.props.title}
    </button>
    ${t?s`<div class="stack">${a}</div>`:null}
  </div>`}function Zn({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return s`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>s`<${se} key=${n.id} node=${n} />`)}
  </div>`}function Qn({node:e}){let t=ie(V),n=Ve(t.path),a=e.props.min_width??320,r=e.props.columns,o=r?`grid-template-columns: repeat(${r}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${a}px, 100%), 1fr))`,l=(e.children??[]).flatMap(d=>d.props.y??[]),i=e.props.addable?n.added.filter(d=>!l.includes(d)).map(d=>({block:"line",id:`added-${d}`,props:{y:d,added:!0},data:{main:{...e.props.template,params:{...e.props.template.params,y:[d]}}}})):[],c=Yt([...e.children??[],...i],n.order[e.id]),u=(d,p)=>{let $=c.map(f=>f.id).filter(f=>f!==d);$.splice($.indexOf(p),0,d),qt(t.path,e.id,$)};return s`<div class="grid" style=${o}>
    ${c.map(d=>s`<${Fs} key=${d.id} node=${d} path=${t.path} span=${n.spans[d.id]??d.props.span??1}
      columns=${r} onDrop=${p=>p!==d.id&&u(p,d.id)} />`)}
    ${e.props.addable&&!!1?s`<${js} path=${t.path} shown=${[...l,...n.added]} />`:null}
  </div>`}var wt=[1,2,"full"];function Fs(e){let[t,n]=h(!1),a=wt[(wt.indexOf(e.span)+1)%wt.length],r=o=>o==="full"?"full width":`${o} column${o===1?"":"s"}`;return s`<div class=${`cell span-${e.span}${t?" drop":""}`}
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
  </div>`}function js(e){let t=y({method:"keys",params:{from:e.path},scope:e.path}).data,n=(t?.metrics?.rows??[]).map(a=>a[0]).filter(a=>!e.shown.includes(a));return t&&!n.length?null:s`<div class="add-chart">
    <span class="add-chart-label"><${v} name="plus" size=${16} /> Add a chart</span>
    <${Ge} single options=${n} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
      onChange=${([a])=>qe(e.path,r=>({added:[...r.added,a]}))} />
  </div>`}function es({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[a,r]=h(()=>t.find(i=>i.id===n())?.id??t[0]?.id),o=i=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(i)}`),r(i)},l=t.find(i=>i.id===a)??t[0];return Re?s`<div class="stack">${t.map(i=>s`<${se} key=${i.id} node=${i} />`)}</div>`:s`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(i=>s`<button type="button" role="tab" id=${`tab-${i.id}`} aria-selected=${i.id===l?.id}
          aria-controls=${`panel-${i.id}`} onClick=${()=>o(i.id)}>${i.props.title??i.id}</button>`)}
    </div>
    ${l?s`<div class="stack" role="tabpanel" id=${`panel-${l.id}`} aria-labelledby=${`tab-${l.id}`}>
          ${(l.children??[]).map(i=>s`<${se} key=${i.id} node=${i} />`)}
        </div>`:null}
  </div>`}var Ws={section:Jn,row:Zn,grid:Qn,line:ln,table:pn,stat:mn,images:Xn,text:Yn,proposal:In,note:Fn,output:Kn,memory:zn,groups:Bn,notes:Hn,tabs:es,scatter:cn,bar:dn,histogram:un,data_table:sn,timeline:an,custom:qn,markdown:Un};function se({node:e}){return s`<${Gt} node=${e} blocks=${Ws} />`}function ts(e,t){let n=e.split(`
`),a=t.split(`
`),r=n.length,o=a.length,l=Array.from({length:r+1},()=>new Uint32Array(o+1));for(let d=r-1;d>=0;d--)for(let p=o-1;p>=0;p--)l[d][p]=n[d]===a[p]?l[d+1][p+1]+1:Math.max(l[d+1][p],l[d][p+1]);let i=[],c=0,u=0;for(;c<r&&u<o;)n[c]===a[u]?(i.push({kind:"same",text:n[c]}),c++,u++):l[c+1][u]>=l[c][u+1]?i.push({kind:"removed",text:n[c++]}):i.push({kind:"added",text:a[u++]});for(;c<r;)i.push({kind:"removed",text:n[c++]});for(;u<o;)i.push({kind:"added",text:a[u++]});return i}function ns(e,t=3){let n=[],a=0;for(;a<e.length;){if(e[a].kind!=="same"){n.push(e[a++]);continue}let r=a;for(;r<e.length&&e[r].kind==="same";)r++;let o=a===0?0:t,l=r===e.length?0:t;r-a>o+l+1?n.push(...e.slice(a,a+o),{kind:"skip",count:r-a-o-l},...e.slice(r-l,r)):n.push(...e.slice(a,r)),a=r}return n}var kt={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",timeline:"timeline",proposal:"predictions"};function ss(e){if(kt[e.block])return kt[e.block];if(e.block==="row"||e.block==="grid"){if(e.props.addable)return"charts";let n=new Set((e.children??[]).map(r=>kt[r.block])),[a]=n;if(n.size===1&&a)return a}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function at(e){let t=y(ze(e.path)),n=re(),a=R(t.data),r=Me(()=>je(a.map(d=>d["run.id"]),n),[t.data,n]),o=Me(()=>new Map(a.map(d=>[d["run.id"],d["run.name"]??d["run.id"]])),[t.data]),l=e.plain?"view plain":"sections view";if(!e.view)return s`<div class=${l}>${e.before}
      ${e.plain?s`<div class="skeleton late" style="block-size: 320px"></div>`:s`<${B} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let i={path:e.path,colors:r,names:o,metrics:e.view.metrics??{}},c=e.view.view;if(e.plain)return s`<div class=${l}><${V.Provider} value=${i}><${se} node=${c} /><//></div>`;let u=c.block==="section"&&!c.props.title?c.children??[]:[c];return s`<div class=${l}>${e.before}
    <${V.Provider} value=${i}>
      ${u.map(d=>{let p=ss(d);return s`<${B} key=${d.id} label=${p}><${We.Provider} value=${p}><${se} node=${d} /><//><//>`})}
    <//>
  </div>`}function as(e){if(null)return s`<div class="view-source small"><${v} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=D(G),a=n.page==="group"&&n.version,r=t.versions?s`<a href=${k(e.path,{history:!0})}><${v} name="history" size=${14} /> history (${t.versions})</a>`:null,o;switch(t.source){case"draft":o=s`draft <b>${t.draft}</b>`;break;case"view":o=s`${t.title?s`<em>${t.title}</em> · `:null}saved ${K(he(t.version))} by ${t.author??"unknown"}`;break;default:o=s`the built-in view`}return s`<div class="view-source small">
    <${v} name="layout" size=${14} /><span>${o}</span>
    ${a?s`<a href=${k(e.path)}>an older version · show the current one</a>`:null}
    ${r}
    ${t.outdated?.length&&!a?s`<${Gs} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||a?null:s`<${Vs} path=${e.path} />
        <${qs} path=${e.path} view=${t} />`}
  </div>`}function Gs(e){let[t,n]=h(null),a=e.outdated.map(o=>o.name).join(", ");return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{await yn(e.path)}catch(o){n(o.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${a} exists; update re-pins this view to it (a new version)`}>
      <${v} name="update" size=${14} /> update ${a}</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function Vs(e){let[t,n]=h(null);return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{Se.set(await Xe(e.path,null,""))}catch(r){n(r.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${v} name="file-text" size=${14} /> add text</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function qs(e){let t=Ve(e.path),n=Vt(t),[a,r]=h(!1),[o,l]=h(e.view.title??""),[i,c]=h(e.view.finding??""),[u,d]=h(null),[p,$]=h(!1);if(!n&&!a)return null;let f=async S=>{S.preventDefault(),$(!0),d(null);try{let C={charts:t.charts,added:t.added,order:t.order,spans:t.spans};await A("save_view",{path:e.path,prefs:C,title:o,finding:i}),qe(e.path,()=>({view:{},charts:{},added:[],order:{},spans:{}})),we(w=>["view","view_history","summary"].includes(w.method)&&w.scope===e.path),r(!1)}catch(C){d(C.message)}finally{$(!1)}};return a?s`<form class="save-form" onSubmit=${f}>
    <${Ie} label="Title"><input value=${o} onInput=${S=>l(S.target.value)} /><//>
    <${Ie} label="Finding"><input value=${i} placeholder="the key result in one sentence"
        onInput=${S=>c(S.target.value)} /><//>
    <div class="save-actions">
      <${ne} type="submit" icon=${p?"hourglass":"save"} disabled=${p}>${p?"Saving\u2026":"Save as view"}<//>
      <${ne} icon="x" kind="quiet" onClick=${()=>r(!1)}>Cancel<//>
      ${u?s`<span class="bad-text small">${u}</span>`:null}
    </div>
  </form>`:s`<${ne} icon="save" class="save-view" onClick=${()=>r(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function rs(e){let t=y(_n(e.path)),n=t.data?.entries??[],[a,r]=h(null),o=a??n.slice(0,2).map(i=>i.version).reverse(),l=i=>{let c=o.includes(i)?o.filter(u=>u!==i):[...o,i].slice(-2);r(c.sort())};return t.status==="error"?s`<${O} kind="error">${t.error}<//>`:s`<section class="history">
    <h2 class="history-title heading"><${v} name="history" size=${16} /> View history</h2>
    ${t.data&&!n.length?s`<${O}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((i,c)=>s`<li key=${i.version} class=${o.includes(i.version)?"picked":""}>
          <label><input type="checkbox" checked=${o.includes(i.version)} onChange=${()=>l(i.version)} />
            <span class="num muted" data-tip=${i.version}>${K(i.time)}</span>
            <b>${i.title??"untitled"}</b><span class="muted">${i.author??""}</span>
            ${i.message?s`<span>${i.message}</span>`:null}</label>
          <a href=${c===0?k(e.path):k(e.path,{version:i.version})}
            onClick=${u=>{u.preventDefault(),_(c===0?k(e.path):k(e.path,{version:i.version}))}}>${c===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${o.length===2?s`<${Xs} path=${e.path} a=${o[0]} b=${o[1]} />`:null}
  </section>`}function Xs(e){let t=i=>({method:"view_show",params:{group:e.path,version:i},scope:e.path}),n=y(t(e.a)).data,a=y(t(e.b)).data,r=y(pe(e.path,e.a)).data,o=y(pe(e.path,e.b)).data,l=n&&a?ns(ts(n.yaml,a.yaml)):[];return s`<div class="compare">
    <h3 class="block-title heading">Changes from ${K(he(e.a))} to ${K(he(e.b))}</h3>
    <pre class="diff code">${l.map(i=>i.kind==="skip"?s`<div class="diff-skip">⋯ ${i.count} unchanged lines</div>`:s`<div class=${`diff-${i.kind}`}>${i.kind==="added"?"+ ":i.kind==="removed"?"\u2212 ":"  "}${i.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${r?.title??e.a}</h3><${at} path=${e.path} view=${r} plain /></div>
      <div><h3 class="block-title heading">${o?.title??e.b}</h3><${at} path=${e.path} view=${o} plain /></div>
    </div>
  </div>`}function os(e){return T(()=>{document.title=`${e.path==="."?"local":e.path} \xB7 Beamtime`},[e.path]),e.history?s`<div class="page"><div class="sections">
      <${B} label=${is(e.path)}><${yt} path=${e.path} /><//>
      <${B} label="history"><${rs} path=${e.path} /><//>
    </div></div>`:s`<div class="page">
    <${Ys} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function Ys(e){let t=y(pe(e.path,e.version,e.draft));T(()=>{t.status==="ready"&&requestAnimationFrame(Pt)},[t.status==="ready"]);let n=s`
    <${B} label=${is(e.path)}>
      <${yt} path=${e.path} finding=${t.data?.finding} />
      ${t.data?s`<${as} path=${e.path} view=${t.data} />`:null}
    <//>
    ${le(e.path.split("/").pop()??"")?null:s`<${Wn} path=${e.path} />`}`;return t.status==="error"?s`<div class="sections">${n}
      <${B} label="view">
        ${Js(e.path,t.error)?s`<${O} kind="warning">${t.error} The page fills in once the remote answers again.<//>`:s`<${O} kind="error">${t.error}<//>`}
      <//>
    </div>`:s`<${at} path=${e.path} view=${t.data} before=${n} />`}function is(e){return le(e.split("/").pop()??"")?"run":"group"}function Js(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function ls(e){T(()=>{ye(pe(e.id)).then(n=>_(k(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=y(pe(e.id));return t.status==="error"?s`<div class="page"><${O} kind="error">${t.error}<//></div>`:s`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var Zs={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},xt=20,Ce=-1,Qs=[["day",86400],["week",7*86400],["month",30*86400]];function ds(e){let t=R(y(oe()).data).map(i=>i.path),n=y({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),a=y({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});T(()=>{document.title="Timeline \xB7 Beamtime"},[]);let r=Date.now()/1e3,o=R(n.data).filter(i=>i["run.created_at"]).map((i,c)=>({id:i["run.id"],name:i["run.name"]??i["run.id"],group:i["run.group"],status:i["run.status"],start:Date.parse(i["run.created_at"])/1e3,end:i["run.ended_at"]?Date.parse(i["run.ended_at"])/1e3:r,lane:c})),l=(a.data?.entries??[]).map(i=>({id:i.id,type:i.type,group:i.group,description:i.description,t:Date.parse(he(i.id))/1e3}));return s`<div class="page timeline-page"><div class="sections">
    <${B} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${Ie} label="Group" inline>
          <select value=${e.from} onChange=${i=>_(Ae(i.target.value),{replace:!0})}>
            ${t.map(i=>s`<option value=${i}>${i==="."?"everything":i}</option>`)}
          </select><//>
        <span class="muted small">${o.length} runs · ${l.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${B} label="runs">
      ${n.status==="error"?s`<${O} kind="error">${n.error}<//>`:null}
      ${n.data&&a.data?s`<${ea} bars=${o} marks=${l} />`:s`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function ea(e){let t=re(),n=H(null),a=[...e.bars.flatMap(w=>[w.start,w.end]),...e.marks.map(w=>w.t)],r=a.length?cs(Math.min(...a),Math.max(...a)):cs(Date.now()/1e3-86400,Date.now()/1e3),[o,l]=h(r),i=e.bars.length,c=Math.min(900,Math.max(160,(i+1.5)*xt+40)),d=rn(n,on,t?(w=>{let E=tn(o[0],o[1]),m=g=>w.colors[Zs[g]??"muted"],b=g=>w.colors[g==="verdict"?"good":g==="decision"?"accent":g==="question"?"warn":"muted"];return{style:Ht(w),height:c,x:{range:o,log:!1,format:g=>nn(g,E.step),splits:E.at},y:{range:[Ce-.8,i+.5],log:!1,reverse:!0,size:150,splits:i<=40?[Ce,...e.bars.map(g=>g.lane)]:[Ce],format:g=>g===Ce?"notes":ra(e.bars[Math.round(g)]?.name??"")},draw:({ctx:g,x:I,y:j,px:U,focused:P})=>{let W=xt*.62*U;for(let N of e.bars){let Q=I(N.start),fe=Math.max(3*U,I(N.end)-Q);g.fillStyle=P!==null&&P!==N.id?Bt(m(N.status),.35):m(N.status),g.beginPath(),g.roundRect(Q,j(N.lane)-W/2,fe,W,3*U),g.fill()}for(let N of e.marks){let Q=I(N.t),fe=j(Ce),z=(P===N.id?6:4.5)*U;g.fillStyle=b(N.type),g.beginPath(),g.moveTo(Q,fe-z),g.lineTo(Q+z,fe),g.lineTo(Q,fe+z),g.lineTo(Q-z,fe),g.closePath(),g.fill()}},hit:(g,I,j,U)=>{if(Math.abs(I-U(Ce))<xt/2){let N=aa(e.marks,Q=>Math.abs(j(Q.t)-g),8);return N?{key:N.id,rows:na(N)}:null}let P=Math.round((I-U(0))/(U(1)-U(0))),W=e.bars.find(N=>N.lane===P&&j(N.start)-3<=g&&g<=Math.max(j(N.end),j(N.start)+3)+3);return W?{key:W.id,rows:ta(W)}:null},onClick:g=>{let I=e.marks.find(j=>j.id===g);I?_(k(I.group,{drawer:!0})):_(ce(g))}}})(t):null,[o,e.bars,e.marks],t),p=w=>{if(!d.current)return;w.preventDefault();let E=d.current.xAt(w.clientX),m=Math.exp(w.deltaY*.0015);l(([b,g])=>St([E-(E-b)*m,E+(g-E)*m],r))},$=H(null),f=w=>$.current={x:w.clientX,range:o},S=w=>{if(!$.current||!d.current||!(w.buttons&1))return;let E=(w.clientX-$.current.x)*d.current.xPerPixel(),[m,b]=$.current.range;Math.abs(w.clientX-$.current.x)>3&&l(St([m-E,b-E],r))},C=Math.max(...a,Date.now()/1e3);return s`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${Qs.map(([w,E])=>s`<button type="button" role="radio" aria-checked=${Math.abs(o[1]-o[0]-E)<1}
          onClick=${()=>l(St([C-E,C+E*.02],[Math.min(r[0],C-E),r[1]]))}>last ${w}</button>`)}
      <button type="button" role="radio" aria-checked=${o[0]===r[0]&&o[1]===r[1]} onClick=${()=>l(r)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${c}px`}
      onWheel=${p} onPointerDown=${f} onPointerMove=${S} onPointerUp=${()=>$.current=null}></div>
    <p class="muted small">${sa(t)}</p>
  </div>`}function ta(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:K(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:ke(e.end-e.start),color:null}]}function na(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:K(new Date(e.t*1e3).toISOString()),color:null}]}function sa(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function aa(e,t,n){let a=null,r=n;for(let o of e){let l=t(o);l<r&&([a,r]=[o,l])}return a}function cs(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function St([e,t],n){let a=Math.min(n[1]-n[0],Math.max(60,t-e)),r=Math.max(n[0],Math.min(e,n[1]-a));return[r,r+a]}function ra(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function us(){let e=D(Pe),t=H(null);if(T(()=>{let r=t.current;if(!r||!e)return;r.showModal();let o=()=>Pe.set(null);return r.addEventListener("close",o),()=>r.removeEventListener("close",o)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},a=String(n.props.title??n.props.y??"Chart");return s`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${a} closedby="any">
    <${V.Provider} value=${e.view}><${se} node=${n} /><//>
  </dialog>`}function ms(e,t){let n=e.toLowerCase(),a=t.toLowerCase();if(!n)return 1;let r=a.indexOf(n);if(r>=0)return 100-Math.min(r,50)-a.length/100;let o=0,l=0;for(let i of a)if(i===n[o]?o++:o>0&&l++,o===n.length)return 40-Math.min(l,39);return 0}function $s(e){let[t,n]=h(e.query),[a,r]=h(0),o=H(null),l=R(y(oe()).data),i=R(y(tt()).data);T(()=>{let m=o.current;m.showModal();let b=()=>Y.set(null);m.addEventListener("close",b);let g=!1,I=P=>{let W=m.getBoundingClientRect();return P.clientX<W.left||P.clientX>W.right||P.clientY<W.top||P.clientY>W.bottom},j=P=>g=I(P),U=P=>g&&I(P)&&m.close();return"closedBy"in HTMLDialogElement.prototype||(m.addEventListener("pointerdown",j),m.addEventListener("pointerup",U)),()=>{m.removeEventListener("close",b),m.removeEventListener("pointerdown",j),m.removeEventListener("pointerup",U)}},[]);let c=()=>o.current?.close(),u=m=>()=>_(m),d=G.value,p=d.page==="group"?d.path:".",$=(m,b,g,I)=>({section:"Commands",label:m,detail:b,sym:{icon:g,tone:"muted",label:m},run:I}),S=[...l.map(m=>({section:"Groups",label:m.path==="."?"local":m.path,detail:`${m.runs} runs${m.proposal?` \xB7 ${m.proposal}`:""}`,sym:M("research",m.status),run:u(k(m.path))})),...i.map(m=>({section:"Runs",label:m["run.name"]??m["run.id"],detail:`${m["run.status"]} \xB7 ${m["run.path"]}`,sym:M("run",m["run.status"]),run:u(k(m["run.path"]))})),$("Theme: light","","sun",()=>Fe("light")),$("Theme: dark","","moon",()=>Fe("dark")),$("Theme: follow the system","","monitor",()=>Fe("system")),$("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),$("Show notes and timeline","i","file-text",u(k(p,{drawer:!0}))),$("Show or hide the sidebar","\u2318B","panel-left",()=>X.set(!X.value)),$(ee.value?"Resume live updates":"Pause live updates","p",ee.value?"play":"pause",()=>ee.set(!ee.value)),$("Keyboard shortcuts","?","keyboard",()=>me.set(!0)),$("Settings","","settings",u("/settings/appearance"))].map(m=>({it:m,s:Math.max(ms(t,m.label),ms(t,m.detail)*.5)})).filter(m=>m.s>0).sort((m,b)=>b.s-m.s||ps(m.it.section)-ps(b.it.section)).slice(0,60).map(m=>m.it),C=m=>{m&&(c(),m.run())},w=m=>{if(m.key==="ArrowDown")r(Math.min(S.length-1,a+1));else if(m.key==="ArrowUp")r(Math.max(0,a-1));else if(m.key==="Enter")C(S[a]);else return;m.preventDefault()},E="";return s`<dialog class="sheet" ref=${o} aria-label="Search" closedby="any">
    <div class="palette-input"><${v} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${S[a]?`pal-${a}`:void 0}
        onInput=${m=>{n(m.target.value),r(0)}} onKeyDown=${w} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${S.map((m,b)=>{let g=m.section!==E&&!t?E=m.section:null;return s`${g?s`<li class="palette-head small" role="presentation">${g}</li>`:null}
          <li id=${`pal-${b}`} class="item" role="option" aria-selected=${b===a}
              onMouseMove=${()=>r(b)} onClick=${()=>C(m)}>
            <${L} spec=${m.sym} /><span class="label">${m.label}</span><span class="detail small">${m.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function ps(e){return["Groups","Runs","Commands"].indexOf(e)}function rt(e,t=[]){let n=new Map,a=(o,l={})=>({path:o,name:o==="."?"local":o.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let o of e)n.set(o.path,a(o.path,o));n.has(".")||n.set(".",a("."));for(let o of t)o.name!=="local"&&(n.has(o.name)||n.set(o.name,a(o.name)),Object.assign(n.get(o.name),{state:o.state,error:o.error}));for(let o of n.values()){if(J(o.path))continue;let l=o.path.lastIndexOf("/"),i=l<0?".":o.path.slice(0,l);(n.get(i)??n.get(Ke(o.path))??n.get(".")).children.push(o)}for(let o of n.values())o.children.sort((l,i)=>l.name.localeCompare(i.name));let r=[...n.values()].filter(o=>o.path!=="."&&J(o.path)).sort((o,l)=>o.name.localeCompare(l.name));return[n.get("."),...r]}function fs(e,t,n){let a=[],r=n.toLowerCase(),o=l=>{(!r||l.path.toLowerCase().includes(r)||hs(l,r))&&(a.push(l),(r||t.has(l.path)||J(l.path))&&l.children.forEach(o))};return e.forEach(o),a}function hs(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||hs(n,t))}function gs(e,t){if(J(t))return e;let n=t.lastIndexOf("/"),a=n<0?".":t.slice(0,n),r=o=>o.path===a?o:o.children.map(r).find(l=>l)??null;return e.map(r).find(o=>o)?.children??[]}function vs(e){return J(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function bs(){let e=D(G),t=y(oe()),[n,a]=h(()=>new Set(Ne("open",[]))),[r,o]=h(""),l=H(null),i=e.page==="group"?e.path:null,c=rt(R(t.data),t.data?.meta?.sources??[]),u=fs(c,la(n,i),r),d=($,f)=>{let S=new Set(n);f??!S.has($)?S.add($):S.delete($),De("open",[...S]),a(S)};return s`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${v} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${r} aria-label="Filter groups"
        onInput=${$=>o($.target.value)} />
    </label>
    <div class="tree" ref=${l} onKeyDown=${$=>{let f=[...l.current?.querySelectorAll("a.tree-item")??[]],S=f.indexOf(document.activeElement),C=u[S];switch($.key){case"ArrowDown":f[Math.min(f.length-1,S+1)]?.focus();break;case"ArrowUp":f[Math.max(0,S-1)]?.focus();break;case"ArrowRight":C?.children.length&&d(C.path,!0);break;case"ArrowLeft":C&&n.has(C.path)?d(C.path,!1):C&&f[u.findIndex(w=>w.path===ia(C.path))]?.focus();break;default:return}$.preventDefault()}} role="tree">
      ${u.map($=>s`<${oa} key=${$.path} node=${$} current=${$.path===i}
        open=${n.has($.path)||!!r} onToggle=${()=>d($.path)} />`)}
    </div>
  </nav>`}function oa(e){let t=e.node,n=()=>Be(t.path),a=t.children.length>0&&!J(t.path);return s`<a class=${`tree-item${e.current?" current":""}${t.path.startsWith("@")&&J(t.path)?" source-root":""}`} href=${k(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${a?e.open:void 0}
      style=${`padding-inline-start:${6+vs(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${r=>{r.metaKey||r.ctrlKey||(r.preventDefault(),_(k(t.path)))}}>
    <span class="twisty" onClick=${r=>{r.preventDefault(),r.stopPropagation(),e.onToggle()}}>
      ${a?s`<${v} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    <span class="tree-name">${t.name}</span>
    ${t.state==="unreachable"?s`<${L} spec=${{icon:"cloud-off",tone:"muted",label:`Unreachable: ${t.error??"no answer"}`}} size=${14} />`:null}
    <span class="tree-marks">
      ${t.running?s`<${L} spec=${M("run","running")} size=${14} />`:null}
      ${t.failed?s`<${L} spec=${{...M("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function ia(e){if(J(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function la(e,t){if(!t||t===".")return e;let n=new Set(e),a=t.split("/");for(let r=1;r<a.length;r++)n.add(a.slice(0,r).join("/"));return n}function ws(){let e=D(G),t=D(X),n=D(Y),a=D(me),r=H(null);T(()=>Rt(()=>r.current),[]),T(()=>(addEventListener("keydown",ys),()=>removeEventListener("keydown",ys)),[]);let o=e.page==="group"&&e.drawer,l;switch(e.page){case"group":l=s`<${os} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":l=s`<${ls} id=${e.id} />`;break;case"settings":l=s`<${Sn} />`;break;case"timeline":l=s`<${ds} key=${e.from} from=${e.from} />`;break;default:l=s`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return de||!1?s`<main class="main render-main" ref=${r}>${l}</main>`:s`<div class=${`shell${t?"":" no-sidebar"}${o?" with-drawer":""}`}>
    <${Rn} />
    ${t?s`<${bs} />`:null}
    <main class="main" ref=${r}>${l}</main>
    ${o?s`<${jn} path=${e.path} run=${e.run} />`:null}
    <${Pn} />
    ${n!==null?s`<${$s} query=${n} />`:null}
    ${a?s`<${da} />`:null}
    <${us} />
  </div>`}function ys(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),Y.set(Y.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),X.set(!X.value);return}if(e.key==="Escape"){if(Y.value!==null||me.value)return;let a=G.value;return a.page==="group"&&a.run?_(k(a.path,{drawer:!0}),{replace:!0}):a.page==="group"&&a.drawer?_(k(a.path),{replace:!0}):void 0}if(t||e.altKey||xn(e)||Y.value!==null||me.value)return;let n=G.value;switch(e.key){case"/":e.preventDefault(),Y.set("");break;case"?":me.set(!me.value);break;case"p":ee.set(!ee.value);break;case"i":n.page==="group"&&_(k(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":X.set(!X.value);break;case"[":case"]":n.page==="group"&&ca(n.path,e.key==="]"?1:-1);break}}async function ca(e,t){let n=await ye(oe()),a=gs(rt(R(n),n?.meta?.sources??[]),e),r=a.findIndex(l=>l.path===e),o=a[r+t];o&&_(k(o.path))}function da(){let e=H(null);return T(()=>{let t=e.current;t.showModal();let n=()=>me.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),s`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${Ye.map(([t,n])=>s`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${ne} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}Ot();if(de){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(ue.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>_e.n,It&&Ft()}$n();var ua=A("meta").then(e=>(de&&(e={...e,settings:{...e.settings,theme_mode:ue.value}}),Je(e),e));!de&&!!1&&Lt(async()=>{let[e,t]=await Promise.all([ua,A("meta")]);e.bundle!==t.bundle?location.reload():Je(t)});Et(s`<${ws} />`,document.getElementById("app"));
