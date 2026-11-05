import{$ as re,$a as hn,A as Rt,Aa as qt,B as Pt,Ba as pt,C as xe,Ca as qe,D as le,Da as Xe,E as S,Ea as Xt,F as Ke,Fa as Yt,G as ce,Ga as Jt,H as _e,Ha as Zt,I as ve,Ia as Qt,J as W,K as V,L as Ot,La as en,Ma as tn,N as D,Na as nn,O as It,Oa as sn,P as zt,Pa as an,Q as de,Qa as rn,R as Le,Ra as on,S as Bt,Sa as ln,T as Ue,U as lt,Ua as cn,V as ue,Va as dn,W as Ut,Wa as un,X as ct,Xa as mn,Y as Fe,Ya as pn,Z as X,Za as $n,_ as Y,_a as fn,aa as je,ba as Ft,c as Tt,ca as Re,d as s,da as Pe,e as g,f as E,fa as jt,g as Mt,ga as Wt,h as O,ha as b,i as Ne,ia as _,j as ie,ja as We,ka as te,la as I,m as ge,ma as R,n as N,na as Oe,o as ye,oa as G,p as we,pa as Gt,qa as z,ra as ne,s as K,sa as Ie,t as De,ta as dt,u as ke,ua as Vt,v as it,va as Ge,w,wa as T,x as _t,xa as mt,y as ee,ya as ze,z as Lt,za as Ve}from"./chunks/chunk-KDKMWKC2.js";import{a as Nt,b as Dt}from"./chunks/chunk-O2K4N3UR.js";import{e as Ht,i as At,j as Kt,k as F,n as fe,o as be,p as Se,q as U,r as ut}from"./chunks/chunk-KRR2HWC7.js";import"./chunks/chunk-VC46IEJQ.js";function Ee(e,t){xe(n=>t.includes(n.method)&&n.scope!==null&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var $t=["notes","timeline","groups","check","card","memory_show","status"];async function ft(e,t){let n=e.meta??{};await K("note_add",{group:e.group,type:e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),Ee(e.group,$t)}async function gn(e,t,n,a){await K("note_add",{group:e,type:t,description:n,body:a}),Ee(e,$t)}async function vn(e,t){await K("memory_update",{group:e,body:t}),Ee(e,["memory_show","status"])}async function bn(e,t){let n=await K("proposal_show",{group:e}),a=Object.fromEntries(Object.entries(n.proposal??{}).filter(([r])=>!["schema","author","user","supersedes"].includes(r)));await K("proposal_set",{group:e,proposal:{...a,statement:t}}),Ee(e,["groups","proposal_show","check","summary"])}async function yn(e){await K("note_rm",{note:e.id}),Ee(e.group,$t)}async function wn(e,t,n){await K("name",{run:e,name:n}),Ee(t,["card","runs","groups","summary","series"])}async function Ye(e,t,n){let a=await K("view_text",{path:e,id:t,text:n});return xe(r=>["view","view_history"].includes(r.method)&&r.scope===e),a.id}async function kn(e){await K("view_upgrade",{group:e}),xe(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var Ce=new ge(null);async function xn(e,t){return await K("set",{key:e,value:t}),K("meta")}var J=new ge(ye("sidebar",!0)),Z=new ge(null),me=new ge(!1),Te=new ge(null);J.subscribe(e=>we("sidebar",e));var Sn=ye("visit",Date.now());we("visit",Date.now());function En(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var Je=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var Cs=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function Ze(e){Te.set(e),Ue.set(e.theme),e.settings?.theme_mode&&ue.set(e.settings.theme_mode),ct()}var Cn=0;async function ht(e,t){let n=++Cn;e==="theme_mode"&&(ue.set(t),ct());let a=await xn(e,t);n===Cn&&Ze(a)}function Tn(){let e=N(ue),t=re(),n=N(Te),[a,r]=g(null);E(()=>{document.title="Settings \xB7 Beamtime"},[]);let o=(c,u)=>{r(null),ht(c,u).catch(m=>r(m.message))},l=n?.settings??{},i=(c,u,m)=>s`
    <label class="field-label small" for=${`setting-${c}`}>${u}</label>
    <span class="input body">
      <select id=${`setting-${c}`} value=${l[c]} onChange=${p=>o(c,p.target.value)}>
        ${m.map(p=>s`<option value=${p}>${p}</option>`)}
      </select>
    </span>`;return s`<div class="page settings"><div class="sections">
    <${z} label="settings">
      <h1 class="page-title title" tabindex="-1">Settings</h1>
      <p class="muted small">Changes are written to <code>${l.file??"beamtime.yaml"}</code>, the project's settings.</p>
      ${a?s`<${I} kind="error">${a}<//>`:null}
    <//>
    <${z} label="appearance">
      <div class="settings-rows">
        <span class="field-label small">Mode</span>
        <div class="segmented" role="radiogroup" aria-label="Theme mode">
          ${Cs.map(([c,u,m])=>s`<button type="button" role="radio" aria-checked=${e===c} onClick=${()=>o("theme_mode",c)}>
            <${b} name=${u} size=${15} />${m}</button>`)}
        </div>
        ${i("theme","Theme",n?.themes??[])}
        ${i("colormap","Colormap",n?.colormaps?.sequential??[])}
        ${i("colormap_diverging","Diverging colormap",n?.colormaps?.diverging??[])}
      </div>
      <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files recolor this layout: they go in <code>themes/</code> next to
        beamtime.yaml. Colormaps color numeric groups and heatmaps.</p>
      ${(n?.theme?.problems??[]).map(c=>s`<${I} kind="warning">${c}<//>`)}
    <//>
    <${z} label="figures">
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
    <${z} label="keyboard">
      <table class="kv">${Je.map(([c,u])=>s`<tr><td><kbd class="small">${c}</kbd></td><td>${u}</td></tr>`)}</table>
    <//>
    <${z} label="about">
      <table class="kv">
        <tr><td class="muted">version</td><td>${n?.version}</td></tr>
        <tr><td class="muted">root</td><td><code class="code">${n?.root}</code></td></tr>
        <tr><td class="muted">log dir</td><td><code class="code">${n?.logdir}</code></td></tr>
      </table>
    <//>
  </div></div>`}var oe=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),pe=(e,t=null,n=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{}},scope:e}),gt=e=>({method:"summary",params:{path:e},scope:e}),Qe=e=>({method:"groups",params:{from:e,depth:0},scope:e}),Mn=e=>({method:"check",params:{group:e},scope:e}),Nn=e=>({method:"proposal_show",params:{group:e},scope:e}),et=(e,t)=>({method:"card",params:{run:_e(e,t)},scope:t}),Dn=(e,t)=>({method:"output",params:{run:_e(e,t),tail:30},scope:t}),Be=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),tt=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),_n=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),Ln=()=>({method:"status",params:{},scope:"."}),nt=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function He(e){for(let t of[pe(e),Qe(e),Be(e),gt(e)])it(t);ke(pe(e)).then(t=>{for(let n of Rn(t.view))it(n)}).catch(()=>{})}function Rn(e){return e?[...Ts.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(Rn)]:[]}var Ts=new Set(["line","custom"]),Pn=e=>({method:"view_history",params:{group:e},scope:e});var On={system:"light",light:"dark",dark:"system"},Ms={system:"monitor",light:"sun",dark:"moon"};function In(){let e=N(Te),t=N(ue),n=N(J);return s`<header class="topbar">
    <${G} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>J.set(!n)} />
    <a class="project heading" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>Z.set("")} aria-label="Search (⌘K)">
      <${b} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${Ns} />
      <${G} icon=${Ms[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${On[t]})`}
        onClick=${()=>{ht("theme_mode",On[t])}} />
      <a class="icon-button" href=${Ke(V.value.page==="group"?V.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${b} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${b} name="settings" size=${16} /></a>
    </div>
  </header>`}function Ns(){let t=(w(oe()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?s`${[{name:"local",state:"connected"},...t].map(n=>s`<a class=${`source small ${n.state}`}
      href=${S(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${b} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:s`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${b} name="server" size=${15} /> local</span>`}function Ds(e){let[t,n]=g(Date.now());return E(()=>{let a=setInterval(()=>n(Date.now()),e);return()=>clearInterval(a)},[e]),t}function _s(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function zn(){let e=N(Lt),t=N(ee),n=N(Rt),a=N(V),r=Ds(5e3),o=w(Ln()).data,l=R(w(nt()).data),i=N(Te),c=o?.daemon,u=o?.runs?.running??0,m=l.filter(P=>P["run.status"]==="failed"&&_s(P["run.ended_at"])>Sn).length,p=o?.meta?.freshness,[v,y,C]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&c?["",`live \xB7 updated ${U(new Date(n).toISOString(),r)}`,`beamtime serve, pid ${c.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return s`<footer class="statusbar small">
    <span class="status-item" data-tip=${C}><span class=${`live-dot ${v}`}></span>${y}</span>
    ${u?s`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>Z.set("running")}>
          <${b} name="circle-dot" size=${14} class="tone-accent" />${u} running</button>`:null}
    ${m?s`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>Z.set("failed")}>
          <${b} name="circle-x" size=${14} />${m} failed since your last visit</button>`:null}
    ${p?.behind?s`<span class="status-item warn-text" data-tip=${p.text}><${b} name="hourglass" size=${14} />${p.behind} runs behind</span>`:null}
    ${p?.damaged?.length?s`<span class="status-item warn-text" data-tip=${p.damaged.join(`
`)}><${b} name="triangle-alert" size=${14} />${p.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${a.page==="group"&&a.run?s`<span class="status-item"><${b} name="activity" size=${14} />1 run selected</span>`:null}
    <${G} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>ee.set(!t)} />
    ${i?.outdated?s`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item">${i?.version?`beamtime ${i.version}`:""}</span>
  </footer>`}var Bn=null;function st(e){let t=O(null),[n,a]=g(null),[r,o]=g(!1),[l,i]=g(!1);E(()=>{let p=!0;return Bn??=import("./chunks/md-SW3VT2BQ.js"),Bn.then(v=>v.render(e.text??"")).then(v=>p&&a(v)),()=>{p=!1}},[e.text]),Mt(()=>{let p=t.current;if(!p||!e.clamp)return;let v=()=>i(p.scrollHeight>p.clientHeight+2),y=new ResizeObserver(v);return y.observe(p),()=>y.disconnect()},[e.clamp,n]);let c=e.clamp&&!r,u=`md${c?" clamped":""}`,m=c?`--clamp:${e.clamp}`:"";return s`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?s`<div class=${u} ref=${t} style=${m}>
          ${(e.text??"").split(/\n{2,}/).map(p=>s`<p>${p}</p>`)}
        </div>`:s`<div class=${u} ref=${t} style=${m} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(l||r)?s`<button type="button" class="link small more" onClick=${()=>o(!r)}>${r?"less":"more"}</button>`:null}
  </div>`}function he(e){let[t,n]=g(!!e.startEditing),[a,r]=g(e.value),[o,l]=g(null),[i,c]=g(null),u=O(null),m=O(!1);E(()=>l(null),[e.value]),E(()=>{!t||!u.current||(u.current.focus(),e.startEditing?u.current.select():u.current.setSelectionRange(u.current.value.length,u.current.value.length))},[t]);let[p,v]=g(!1),y=e.locked??void 0,C=$=>{if(!$.target.closest("a, button, input, summary")){if(y)return v(!0);$.preventDefault(),r(o??e.value),c(null),m.current=!1,n(!0)}},P=()=>{m.current=!0,n(!1),c(null),e.onCancel?.()},f=async()=>{if(m.current)return;m.current=!0;let $=e.multiline?a.trim():a.replace(/\s*\n\s*/g," ").trim();if($===e.value.trim()||!$&&!e.multiline)return P();n(!1),l($);try{await e.onSave($)}catch(h){l(null),r($),c(h.message),m.current=!1,n(!0)}},k=$=>{if($.key==="Escape")return $.preventDefault(),$.stopPropagation(),P();$.key!=="Enter"||$.isComposing||$.keyCode===229||(!e.multiline||$.metaKey||$.ctrlKey)&&($.preventDefault(),f())};if(t)return s`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${u} class="edit-field" value=${a} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,a.split(`
`).length+1)):1}
        onInput=${$=>r($.target.value)} onKeyDown=${k} onBlur=${f}></textarea>
      <span class="edit-hint small">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${i?s` · <span class="bad-text">${i}</span>`:null}</span>
    </div>`;let d=o??e.value;return s`<div class=${`editable${y?" locked":""}${o!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${y?`${e.label}: ${y}`:`Edit ${e.label}`}
      data-tip=${y} onClick=${C} onBlur=${()=>v(!1)}
      onKeyDown=${$=>$.key==="Enter"&&$.target===$.currentTarget&&C($)}>
    ${d.trim()?e.render?e.render(d):d:s`<span class="muted">${e.placeholder??"Click to write"}</span>`}
    ${p&&y?s`<span class="edit-hint small locked-why" role="status"><${b} name="lock" size=${14} /> ${y}</span>`:null}
  </div>`}function vt(e){let t=[];if(e.effect!==void 0&&e.effect!==null){let n=e.ci?` [${F(e.ci[0])}, ${F(e.ci[1])}]`:"";t.push(`${e.effect>=0?"+":""}${F(e.effect)}${n}`)}return e.threshold!==void 0&&e.threshold!==null&&t.push(`needs ${e.op} ${F(e.threshold)}`),e.points&&t.push(`${e.points} point${e.points>1?"s":""}`),e.detail&&t.push(e.detail),t.join(" \xB7 ")}function bt(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function Hn({node:e}){let t=Y("proposal"),n=Y("check"),a=t.data,r=n.data;if(!a)return s`<${te} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let o=a.proposal??{},l=(a.versions??[]).filter(c=>c.version!==a.version),i=!e.props.of||e.props.of===".";return s`<${te} title="Predictions" result=${t} class="proposal">
    ${i?null:s`<p class="statement">${o.statement}</p>`}
    ${o.rationale?s`<p class="rationale prose">${o.rationale}</p>`:null}
    <div class="predictions">
      ${(r?.predictions??[]).map(c=>s`<div class="prediction" key=${c.name}>
          <${_} spec=${T("result",c.result)} />
          <span class="pname">${c.name}</span>
          <span class="pdetail num small">${vt(c)}</span>
        </div>`)}
    </div>
    ${l.length?s`<${dt} summary=${`${l.length} earlier version${l.length>1?"s":""}`}>
          ${l.map(c=>s`<p class="small"><code>${c.version}</code> ${c.statement}
            <span class="muted">(${c.runs} runs, check ${c.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function An({node:e}){let t=Y("main"),n=e.data?.main.params.group??".",a=t.data?.chain??[],r=a.find(i=>i.group===n)??null,o=a.filter(i=>i.group!==n),l=r?.notes_since?"out of date":r?`version ${r.versions??1}`:"none yet";return s`<${Oe} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?l:void 0} open=${!1} result=${t}
      action=${s`<${_} spec=${{icon:"circle-help",tone:"muted",label:Rs}} />`}>
    <${he} value=${r?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${i=>s`<${st} text=${i} />`} onSave=${i=>vn(n,i)} />
    ${r&&(r.body?.length>(t.data?.budget??1/0)||r.notes_since>=Ls)?s`<p class="memory-meta small warn-text">${r.body?.length>t.data.budget?`${r.body.length} characters, beyond the budget of ${t.data.budget}`:`${r.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${r?s`<p class="memory-meta small">${r.author} · covers notes until ${r.covers_until?.slice(0,10)}
          ${r.notes_since?s` · <span class="warn-text">${r.notes_since} newer note${r.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${o.length?s`<p class="memory-meta small">Memory above this group: ${o.map((i,c)=>s`${c?", ":""}<a href=${S(i.group)}>${i.group==="."?"local":i.group}</a>`)}</p>`:null}
  <//>`}var Ls=5,Rs="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",Ps="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function Kn({node:e}){let t=Y("main"),n=e.data?.main.params.from??".",a=R(t.data).filter(r=>r.path!==n);return s`<${te} title=${e.props.title} count=${t.data?String(a.length):void 0} result=${t}>
    ${t.data&&!a.length?s`<${I}>No groups below.<//>`:null}
    <div class="group-list">
      ${a.map(r=>{let[o,l]=bt(r.progress),i=(r.failed??0)+(r.killed??0)+(r.lost??0);return s`<a class="group-row" key=${r.path} href=${S(r.path)}
            onPointerEnter=${()=>He(r.path)} onFocus=${()=>He(r.path)}>
          <${_} spec=${T("research",r.status)} />
          <span class="gname heading">${r.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${r.status!=="concluded"?s`<span class=${`tone-${T("research",r.status).tone}`}>${T("research",r.status).label}</span>`:null}
            ${r.check?s`<${_} spec=${T("result",r.check)} word />`:null}
            ${r.verdict?s`<${_} spec=${T("verdict",r.verdict)} />`:null}
            ${o?s`<span data-tip=${l}>${o}</span>`:null}
            <span class="num"><b>${r.runs}</b> runs</span>
            ${r.running?s`<${_} spec=${T("run","running")} />`:null}
            ${i?s`<span class="tone-bad num" data-tip="failed, killed or lost"><${b} name="circle-x" size=${14} /> ${i}</span>`:null}
          </span>
          ${r.proposal?s`<span class="gstatement caption">${r.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function Un({node:e}){let t=Y("main"),n=e.data?.main.params.from??".",[a,r]=g(!1),o=(t.data?.entries??[]).filter(i=>!String(i.state??"").startsWith("superseded")),l=t.data?.meta?.matched??o.length;return s`<${Oe} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(l):void 0} result=${t}
      action=${s`<${_} spec=${{icon:"circle-help",tone:"muted",label:Ps}} />
        ${s`<${G} icon="plus" label="Add a note" onClick=${()=>r(!0)} />`}`}>
    <div class="notes">
      ${a?s`<${zs} group=${n} onDone=${()=>r(!1)} />`:null}
      ${t.data&&!o.length&&!a?s`<p class="muted small">No notes yet.</p>`:null}
      ${o.map(i=>s`<${at} key=${i.id} note=${i} scope=${n} />`)}
      ${t.data?.more&&e.data?s`<${Fn} call=${e.data.main} before=${o[o.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var Os=20;function Fn(e){let[t,n]=g(!1),a=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:Os}}:null,r=w(a);if(!t)return s`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(r.status==="error")return s`<p class="bad-text small">${r.error}</p>`;let o=r.data?.entries??[];return s`${r.data?null:s`<div class="skeleton" style="block-size: 40px"></div>`}
    ${o.map(l=>s`<${at} key=${l.id} note=${l} scope=${e.scope} />`)}
    ${r.data?.more?s`<${Fn} call=${e.call} before=${o[o.length-1]?.id} scope=${e.scope} />`:null}`}var Is=["observation","idea","question","decision"];function zs(e){let[t,n]=g("observation"),[a,r]=g(""),[o,l]=g(""),[i,c]=g(null),[u,m]=g(!1),p=async y=>{if(y.preventDefault(),!a.trim())return c("give the note a title");m(!0);try{await gn(e.group,t,a.trim(),o.trim()),e.onDone()}catch(C){c(C.message),m(!1)}};return s`<form class="note new-note" onSubmit=${p} onKeyDown=${y=>{y.key==="Escape"&&e.onDone(),y.key==="Enter"&&(y.metaKey||y.ctrlKey)&&p(y)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${t} aria-label="Note type" onChange=${y=>n(y.target.value)}>
        ${Is.map(y=>s`<option value=${y}>${y}</option>`)}
      </select></span>
      <span class="input body new-note-field"><input class="new-note-title" value=${a} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${y=>r(y.target.value)} /></span>
    </div>
    <span class="input small"><textarea class="new-note-body" rows="4" value=${o} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${y=>l(y.target.value)}></textarea></span>
    <div class="save-actions">
      <${ne} type="submit" icon=${u?"hourglass":"plus"} disabled=${u}>${u?"Adding\u2026":"Add note"}<//>
      <${ne} icon="x" kind="quiet" onClick=${e.onDone}>Cancel<//>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${i?s`<span class="bad-text small">${i}</span>`:null}
    </div>
  </form>`}function at(e){let t=e.note,[n,a]=g(!!e.open),[r,o]=g(!1),l=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,i=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),c=t.meta?.author;return s`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${u=>!u.target.closest(".editable, a, .note-delete")&&a(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${b} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${_} spec=${T("note",t.type)} />
      <${he} value=${t.description} label="the note's title" class="note-title heading" render=${Hs}
        onSave=${u=>ft(t,{description:u})} />
      ${t.overall?s`<${_} spec=${T("verdict",t.overall)} />`:null}
      ${t.state?s`<${Gt} tone="warn">${t.state}<//>`:null}
      ${l?s`<a class="note-group small" href=${S(l)} data-tip="from this group">${Bs(l,e.scope)}</a>`:null}
      <span class="note-meta small">${c?`${c} \xB7 `:""}${U(i)}</span>
      ${s`<${G} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${r}
        onClick=${u=>{u.stopPropagation(),o(!r)}} />`}
    </div>
    ${r?s`<div class="note-confirm small" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <${ne} icon="trash" kind="danger" onClick=${()=>{yn(t)}}>Delete<//>
          <${ne} icon="x" kind="quiet" onClick=${()=>o(!1)}>Cancel<//>
        </div>`:null}
    ${n?s`<${he} value=${t.body??""} label="the note" multiline class="note-body prose markdown"
          placeholder="Add details in Markdown" render=${u=>s`<${st} text=${u} />`}
          onSave=${u=>ft(t,{body:u})} />`:null}
  </article>`}function Bs(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,a=n.split("/").pop()??n;return le(a)?a.slice(-8):n}function jn({node:e}){let t=Y("main"),n=t.data?.lines??[],a=t.data?.meta??{},r=s`<${b} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${a.total_lines??n.length} lines${(a.shown??0)<(a.total_lines??0)?`, last ${a.shown}`:""}`:""}</span>`;return s`<${te} result=${t}>
    <${dt} summary=${r} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function Wn({node:e}){let t=ie(X);return s`<${te} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${he} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${Ce.value===e.id} onCancel=${()=>Ce.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>s`<${st} text=${n} />`}
      onSave=${n=>(Ce.set(null),Ye(t.path,e.id,n))} />
  <//>`}function Gn({node:e}){return s`<${I} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function Hs(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let a=n.slice(2,-2),[r]=a.split(/[#@]/),o=r.split("/").pop()??"";return s`<a href=${le(o)?ce(o):S(r)}>${a}</a>`}return n.startsWith("`")?s`<code>${n.slice(1,-1)}</code>`:n})}function Vn(e){let t=()=>D(S(e.path),{replace:!0});return s`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${b} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${G} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?s`<${As} id=${e.run} scope=${e.path} />`:s`<${Ks} path=${e.path} />`}
  </aside>`}function As({id:e,scope:t}){let n=w(et(e,t)).data,a=w(Dn(e,t)).data,r=w(Be(t)).data,o=w({method:"keys",params:{from:t},scope:t}).data,l=re(),i=Ne(()=>je(R(r).map(p=>p["run.id"]),l).get(e),[r,l,e]);if(!n)return s`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let c=n.run,u=Object.entries(n.metrics??{}),m=Ht(i,l);return s`<div class="drawer-body">
    <h3 class="heading"><span class=${m.class} style=${m.style}></span>
      <a href=${ce(e)}>${c.name}</a></h3>
    <p class="facts small">
      <${_} spec=${T("run",c.status)} word />
      <span><b>${be(c.steps)}</b> steps</span>
      <span><b>${Se(c.duration_s)}</b></span>
      <span data-tip=${c.created_at}>${U(c.created_at)}</span>
    </p>
    ${c.error?s`<pre class="log code bad-text">${c.error}</pre>`:null}
    <h4 class="small">Config</h4>
    <${Ve} config=${n.config??{}} varying=${ze(o)} />
    ${u.length?s`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${u.map(([p,v])=>s`<tr><td>${p}</td><td class="num"><b>${F(v.last)}</b></td>
              <td class="num">${F(v.min)}</td><td class="num">${F(v.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?s`<h4 class="small">Cited by</h4>${n.cited_by.map(p=>s`<p class="small"><${_} spec=${T("note",p.type)} /> ${p.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(p=>s`<div class="event small"><span class="muted num">${p.t?.slice(5,16).replace("T"," ")}</span>
        <${b} name=${mt(p.type)} size=${14} /><span>${p.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(a?.lines??[]).join(`
`)}</pre>
  </div>`}function Ks({path:e}){let t=w(tt(e)).data,n=w(_n(e)).data;return s`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?s`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(a=>!String(a.state??"").startsWith("superseded")).map(a=>s`<${at} key=${a.id} note=${a} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(a=>s`<div class="event small"><span class="muted num">${a.t?.slice(5,16).replace("T"," ")}</span>
        <${b} name=${a.kind==="note"?"file-text":mt(a.type)} size=${14} />
        <span>${a.run?s`<a href=${ce(a.run)}>${a.run.slice(-8)}</a> `:null}${a.description??a.type}</span></div>`)}
  </div>`}var yt=["failed","killed","lost"];function wt(e){let t=ve(e.path),n=t==="."?e.path:e.path.slice(t.length+1),a=W(e.path)?[]:n.split("/"),r=a.length&&le(a[a.length-1])?a[a.length-1]:null,o=a.slice(0,-1),l=i=>[...t==="."?[]:[t],...o.slice(0,i+1)].join("/");return s`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${a.length?s`<a href=${S(t)}>${t==="."?"local":t}</a>`:null}
      ${o.map((i,c)=>s`<span>/</span><a href=${S(l(c))}>${i}</a>`)}
    </nav>
    ${r?s`<${js} id=${r} scope=${e.path} />`:s`<${Us} path=${e.path} />`}
    ${e.finding?s`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function Us({path:e}){let t=R(w(Qe(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return s`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=yt.reduce((r,o)=>r+(t[o]??0),0);return s`
    <h1 class="page-title title" tabindex="-1">${n} <${_} spec=${T("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?s`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?s`<span><b>${t.finished}</b> finished</span>`:null}
      ${a?s`<span class="tone-bad" data-tip=${yt.filter(r=>t[r]).map(r=>`${t[r]} ${r}`).join(", ")}>
            <${b} name="circle-x" size=${15} /> <b>${a}</b> ${a===1?yt.find(r=>t[r]):"ended early"}</span>`:null}
      ${t.notes?s`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${Xn} path=${e} />
    </p>`}function qn({path:e}){let t=R(w(Qe(e)).data)[0]??null,n=w(t?.proposal?Mn(e):null).data,a=w(t?.proposal?Nn(e):null).data;if(!t?.proposal)return null;let r=a?.proposal?.rationale,o=a?.versions?.find(c=>c.version===a.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[l,i]=bt(n?.progress?.text??t.progress);return s`<${z} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${he} value=${t.proposal} label="the proposal's statement" locked=${a?o:"Loading the proposal\u2026"}
          render=${c=>s`<span data-tip=${o?void 0:r}>${c}</span>`}
          onSave=${c=>bn(e,c)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(c=>{let u=T("result",c.result),m=vt(c),p=m?`${u.label}: ${m}`:u.label;return s`<span class=${`check small tone-${u.tone}`} key=${c.name} data-tip=${p}
              aria-label=${`${c.name}: ${p}`} tabindex="0"><${b} name=${u.icon} size=${14} />${c.name}</span>`})}
        ${n?.provisional||l?s`<span class="small">
              ${n?.provisional?s`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${l?s`<span class="muted" data-tip=${i}>${n?.provisional?" \xB7 ":""}${l}</span>`:null}
            </span>`:null}
      </div>
      <${Fs} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function Fs(e){let t=w(e.verdict?tt(e.path):null).data;if(!e.verdict)return s`<p class="verdict-line muted">no verdict yet</p>`;let n=T("verdict",e.verdict),a=(t?.entries??[]).find(o=>o.type==="verdict"&&(o.group??e.path)===e.path),r=a?fe(a.id):null;return s`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${b} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${a?s`<span class="small muted" data-tip=${r}>verdict${a.meta?.author?` by ${a.meta.author}`:""}${r?` \xB7 ${U(r)}`:""}</span>`:null}
  </p>`}function js({id:e,scope:t}){let n=w(et(e,t)).data;if(!n)return s`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=n.run,r=()=>{navigator.clipboard?.writeText(a.id)};return s`
    <h1 class="page-title title" tabindex="-1"><${he} value=${a.name??a.id} label="the run's name" class="title-edit"
        onSave=${o=>wn(a.id,t,o.trim())} />
      <${_} spec=${T("run",a.status)} word /></h1>
    ${a.error?s`<p class="bad-text" data-tip=${a.error}>${a.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${be(a.steps)}</b> steps</span>
      <span><b>${Se(a.duration_s)}</b></span>
      <span data-tip=${a.created_at}>${U(a.created_at)}</span>
      <${Xn} path=${t} />
      <${G} icon="copy" label=${`Copy the run id ${a.id}`} onClick=${r} />
      <${Vt} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${Ws(a).map(([o,l])=>s`<tr><td class="muted">${o}</td><td>${l}</td></tr>`)}</table>
        <div class="menu-list">
          <button type="button" onClick=${()=>D(S(t,{run:a.id}),{replace:!0})}>
            <${b} name="panel-right" size=${15} /> Open in the side panel</button>
          <button type="button" onClick=${r}><${b} name="copy" size=${15} /> Copy the run id</button>
          ${a.git?.commit?s`<button type="button" onClick=${()=>navigator.clipboard?.writeText(a.git.commit)}>
            <${b} name="git-commit" size=${15} /> Copy the commit</button>`:null}
        </div>
      <//>
    </div>
    ${(n.proposals??[]).length?s`<div class="checks">
          ${n.proposals.map(o=>{let l=T("result",o.check);return s`<a class=${`check small tone-${l.tone}`} href=${S(o.group)} data-tip=${o.statement}>
              <${b} name=${l.icon} size=${14} />${o.group==="."?"own proposal":o.group}
              ${o.verdict?s`<${_} spec=${T("verdict",o.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function Xn({path:e}){let t=w(gt(e)).data?.summary;if(!t)return null;let n=Object.entries(t.config??{}).map(([o,l])=>`${ut(o)} ${F(l)}`).join(", "),a=le(e.split("/").pop()??""),r=`${t.stat} of ${t.metric} over ${a?"the run":"all runs"}${n?` (${n})`:""}`;return s`<span data-tip=${r}>
    best <b>${ut(`metric.${t.metric}.${t.stat}`)} ${F(t.value)}</b>
    ${a?null:s` · <a href=${ce(t.run)}>${t.name}</a>`}
  </span>`}function Ws(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,a])=>[n,String(a)])}var kt=80;function Yn({node:e}){let t=Y("main"),n=Y(e.data?.keys?"keys":""),a=e.props.mode==="run",r=e.props.title??(a?"Config":"Hyperparameters");return s`<${Oe} id=${`config:${e.id}`} title=${r} open=${e.props.open} result=${t}>
    ${t.data?a?s`<${Ve} config=${t.data.config} varying=${ze(n.data)} />`:s`<${Gs} rows=${t.data.config?.rows??[]} />`:s`<div class="skeleton late" style="block-size: 80px"></div>`}
  <//>`}function Gs({rows:e}){let t=new Set(ze({config:{rows:e}})),n=e.filter(([a])=>t.has(a.replace(/^config\./,"")));return n.length?s`<table class="kv small">${n.map(([a,,r])=>{let o=Array.isArray(r)?r.map(F).join(", "):`${F(r.min)} \u2026 ${F(r.max)} \xB7 ${r.distinct} values`;return s`<tr><td data-tip=${a}>${a.replace(/^config\./,"")}</td>
      <td data-tip=${o.length>kt?o:void 0}>${o.length>kt?`${o.slice(0,kt-1)}\u2026`:o}</td></tr>`})}</table>`:s`<p class="muted small">No config differs between the runs.</p>`}var Jn=15e3;function Zn({node:e}){let t=ie(X),n=re(),[a,r]=Ft(),o=e.props.code,l=w(r&&o?{method:"code",params:o,scope:null}:null),[i,c]=g(null),[u,m]=g(120),[p,v]=g({error:null,warnings:[]}),y=k=>{de&&console.error(`[block ${e.id}] ${k}`),v(d=>({...d,error:k}))},C=O(()=>{});E(()=>{if(!i)return;let k=!0;De.n++;let d=()=>{k&&De.n--,k=!1};C.current=d;let $=setTimeout(()=>{k&&y(`no first render within ${Jn/1e3} s`),d()},Jn);return()=>{clearTimeout($),d()}},[i]),E(()=>{let k=i?.contentWindow;if(!k||l.status!=="ready")return;let d=M=>k.postMessage(M,"*"),$=new Map,h=new nn,A=M=>{if(M.source!==k)return;let x=M.data;switch(x.type){case"hello":d({type:"init",init:{id:e.id,code:l.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:Ut.value,pair:Ue.value,prefs:pt(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics}});break;case"sub":if(!Qt.has(x.call.method)){d({type:"result",id:x.id,result:{status:"error",data:null,error:`${x.call.method} is not available in a custom block`,refreshing:!1}});break}$.get(x.id)?.(),$.set(x.id,_t(x.call,ae=>d({type:"result",id:x.id,result:ae})));break;case"unsub":$.get(x.id)?.(),$.delete(x.id);break;case"navigate":x.url.startsWith("/")&&D(x.url);break;case"height":h.accept(performance.now())?m(Math.max(40,x.height)):B("its height keeps changing, so it is fixed at its last height");break;case"ready":v(ae=>({...ae,blank:x.blank,overflow:x.overflow})),C.current();break;case"warn":B(x.message);break;case"hover":lt.set(x.run);break;case"prefs":JSON.stringify(H.value)!==JSON.stringify(x.prefs)&&H.set(x.prefs);break;case"download":case"snapshot":x.href?en(x.href,x.name)?performance.now()-j>1e3&&(j=performance.now(),Pe().download(x.href,x.name)):B(`a download of ${x.name} was refused: only PNG, SVG and CSV files`):B("it draws no SVG or canvas to download");break;case"figure":Pe().figure(x.spec,x.name).catch(ae=>B(`the PDF failed: ${ae.message}`));break;case"expand":tn(x.node)&&Pe().expand(x.node,t);break;case"error":y(x.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,P)),C.current();break;default:break}},B=M=>{de&&console.warn(`[block ${e.id}] ${M}`),v(x=>x.warnings.includes(M)?x:{...x,warnings:[...x.warnings,M]})},j=-1/0,H=pt(t.path),q=lt.subscribe(M=>d({type:"hover",run:M})),L=H.subscribe(M=>d({type:"prefs",prefs:M}));return addEventListener("message",A),d({type:"ping"}),()=>{q(),L(),removeEventListener("message",A);for(let M of $.values())M()}},[l.status,l.data?.code,i]),E(()=>{let k={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};i?.contentWindow?.postMessage(k,"*")},[t.names,t.colors,t.metrics,i]),E(()=>{n&&i?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let P=typeof o=="object"?o.path??o.block:String(o??"");jt(e.id,{png:()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")});let f=r&&l.status==="ready"&&!p.error;return s`<div ref=${a} class="custom-block">
    <div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${f?s`<span class="chart-tools">
            <${G} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?s`<${G} icon="x" label="Close (Esc)" onClick=${()=>Re.set(null)} />`:s`<${G} icon="maximize" label="Expand" onClick=${()=>Pe().expand(e,t)} />`}
          </span>`:null}
    </div>
    <${te} caption=${e.props.expanded?void 0:e.props.caption} result=${l}>
      ${p.error?s`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${P})</span>
            <pre class="code">${p.error}</pre>
          </div>`:null}
      ${p.warnings.map(k=>s`<${I} kind="warning">${k}<//>`)}
      ${f?s`<div class="custom-frame" data-frame-blank=${p.blank?"1":void 0} data-frame-overflow=${p.overflow?"1":void 0}>
            <iframe key=${l.data.code} ref=${c} sandbox="allow-scripts" ...${Vs()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${u}px`} />
          </div>`:null}
    <//>
  </div>`}function Vs(){if(!!1)return{src:Nt("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1").replace(/@font-face\s*\{[^}]*\}/g,""),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}function Qn({node:e}){let t=Y("main"),n=ie(X),a=t.data?.entries??[];return s`<${te} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!a.length?s`<${I}>No images logged.<//>`:null}
    <div class="images">
      ${a.map(r=>s`<figure key=${`${r.run}/${r.path}`}>
          <img src=${Dt(_e(r.run,n.path),r.path)} alt=${r.caption??e.props.title} loading=${Le?"eager":"lazy"} />
          <figcaption class="small">step ${be(r.step)}${r.caption?` \xB7 ${r.caption}`:""}</figcaption>
        </figure>`)}
    </div>
  <//>`}function es({node:e}){let t=Y("main"),n=t.data?.entries??[];return s`<${te} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?s`<${I}>No text logged.<//>`:null}
    ${n.map(a=>s`<div class="text-entry" key=${`${a.run}/${a.step}`}>
        <div class="muted small">step ${be(a.step)}${a.caption?` \xB7 ${a.caption}`:""}</div>
        <pre class="code">${a.text??""}</pre>
      </div>`)}
  <//>`}function ts({node:e}){let[t,n]=g(Le||e.props.open!==!1),a=s`${(e.children??[]).map(l=>s`<${se} key=${l.id} node=${l} />`)}`,r=ie(We);if(!e.props.title)return s`<div class="stack">${a}</div>`;let o=r===e.props.title.toLowerCase();return s`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${t} aria-label=${o?`${t?"Close":"Open"} ${e.props.title}`:void 0}
        data-tip=${o?`${t?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${()=>n(!t)}>
      <${b} name=${t?"chevron-down":"chevron-right"} size=${16} />${o?null:e.props.title}
    </button>
    ${t?s`<div class="stack">${a}</div>`:null}
  </div>`}function ns({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return s`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>s`<${se} key=${n.id} node=${n} />`)}
  </div>`}function ss({node:e}){let t=ie(X),n=qe(t.path),a=e.props.min_width??320,r=e.props.columns,o=r?`grid-template-columns: repeat(${r}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${a}px, 100%), 1fr))`,l=(e.children??[]).flatMap(m=>m.props.y??[]),i=e.props.addable?n.added.filter(m=>!l.includes(m)).map(m=>({block:"line",id:`added-${m}`,props:{y:m,added:!0},data:{main:{...e.props.template,params:{...e.props.template.params,y:[m]}}}})):[],c=Zt([...e.children??[],...i],n.order[e.id]),u=(m,p)=>{let v=c.map(y=>y.id).filter(y=>y!==m);v.splice(v.indexOf(p),0,m),Yt(t.path,e.id,v)};return s`<div class="grid" style=${o}>
    ${c.map(m=>s`<${qs} key=${m.id} node=${m} path=${t.path} span=${n.spans[m.id]??m.props.span??1}
      columns=${r} onDrop=${p=>p!==m.id&&u(p,m.id)} />`)}
    ${e.props.addable&&!!1?s`<${Xs} path=${t.path} shown=${[...l,...n.added]} />`:null}
  </div>`}var xt=[1,2,"full"];function qs(e){let[t,n]=g(!1),a=xt[(xt.indexOf(e.span)+1)%xt.length],r=o=>o==="full"?"full width":`${o} column${o===1?"":"s"}`;return s`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${o=>{o.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${o=>{o.preventDefault(),n(!1),e.onDrop(o.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${o=>o.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${b} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${r(e.span)}; click for ${r(a)}`}
        aria-label=${`Width ${r(e.span)}`} onClick=${()=>Jt(e.path,e.node.id,a)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${se} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function Xs(e){let t=w({method:"keys",params:{from:e.path},scope:e.path}).data,n=(t?.metrics?.rows??[]).map(a=>a[0]).filter(a=>!e.shown.includes(a));return t&&!n.length?null:s`<div class="add-chart">
    <span class="add-chart-label"><${b} name="plus" size=${16} /> Add a chart</span>
    <${Ge} single options=${n} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
      onChange=${([a])=>Xe(e.path,r=>({added:[...r.added,a]}))} />
  </div>`}function as({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[a,r]=g(()=>t.find(i=>i.id===n())?.id??t[0]?.id),o=i=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(i)}`),r(i)},l=t.find(i=>i.id===a)??t[0];return Le?s`<div class="stack">${t.map(i=>s`<${se} key=${i.id} node=${i} />`)}</div>`:s`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(i=>s`<button type="button" role="tab" id=${`tab-${i.id}`} aria-selected=${i.id===l?.id}
          aria-controls=${`panel-${i.id}`} onClick=${()=>o(i.id)}>${i.props.title??i.id}</button>`)}
    </div>
    ${l?s`<div class="stack" role="tabpanel" id=${`panel-${l.id}`} aria-labelledby=${`tab-${l.id}`}>
          ${(l.children??[]).map(i=>s`<${se} key=${i.id} node=${i} />`)}
        </div>`:null}
  </div>`}var Ys={section:ts,row:ns,grid:ss,line:dn,table:fn,stat:$n,images:Qn,text:es,proposal:Hn,note:Gn,output:jn,config:Yn,memory:An,groups:Kn,notes:Un,tabs:as,scatter:un,bar:mn,histogram:pn,data_table:rn,timeline:on,custom:Zn,markdown:Wn};function se({node:e}){return s`<${qt} node=${e} blocks=${Ys} />`}function rs(e,t){let n=e.split(`
`),a=t.split(`
`),r=n.length,o=a.length,l=Array.from({length:r+1},()=>new Uint32Array(o+1));for(let m=r-1;m>=0;m--)for(let p=o-1;p>=0;p--)l[m][p]=n[m]===a[p]?l[m+1][p+1]+1:Math.max(l[m+1][p],l[m][p+1]);let i=[],c=0,u=0;for(;c<r&&u<o;)n[c]===a[u]?(i.push({kind:"same",text:n[c]}),c++,u++):l[c+1][u]>=l[c][u+1]?i.push({kind:"removed",text:n[c++]}):i.push({kind:"added",text:a[u++]});for(;c<r;)i.push({kind:"removed",text:n[c++]});for(;u<o;)i.push({kind:"added",text:a[u++]});return i}function os(e,t=3){let n=[],a=0;for(;a<e.length;){if(e[a].kind!=="same"){n.push(e[a++]);continue}let r=a;for(;r<e.length&&e[r].kind==="same";)r++;let o=a===0?0:t,l=r===e.length?0:t;r-a>o+l+1?n.push(...e.slice(a,a+o),{kind:"skip",count:r-a-o-l},...e.slice(r-l,r)):n.push(...e.slice(a,r)),a=r}return n}var St={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",config:"config",timeline:"timeline",proposal:"predictions"};function is(e){if(St[e.block])return St[e.block];if(e.block==="row"||e.block==="grid"){if(e.props.addable)return"charts";let n=new Set((e.children??[]).map(r=>St[r.block])),[a]=n;if(n.size===1&&a)return a}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function rt(e){let t=w(Be(e.path)),n=re(),a=R(t.data),r=Ne(()=>je(a.map(m=>m["run.id"]),n),[t.data,n]),o=Ne(()=>new Map(a.map(m=>[m["run.id"],m["run.name"]??m["run.id"]])),[t.data]),l=e.plain?"view plain":"sections view";if(!e.view)return s`<div class=${l}>${e.before}
      ${e.plain?s`<div class="skeleton late" style="block-size: 320px"></div>`:s`<${z} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let i={path:e.path,colors:r,names:o,metrics:e.view.metrics??{}},c=e.view.view;if(e.plain)return s`<div class=${l}><${X.Provider} value=${i}><${se} node=${c} /><//></div>`;let u=c.block==="section"&&!c.props.title?c.children??[]:[c];return s`<div class=${l}>${e.before}
    <${X.Provider} value=${i}>
      ${u.map(m=>{let p=is(m);return s`<${z} key=${m.id} label=${p}><${We.Provider} value=${p}><${se} node=${m} /><//><//>`})}
    <//>
  </div>`}function ls(e){if(null)return s`<div class="view-source small"><${b} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=N(V),a=n.page==="group"&&n.version,r=t.versions?s`<a href=${S(e.path,{history:!0})}><${b} name="history" size=${14} /> history (${t.versions})</a>`:null,o;switch(t.source){case"draft":o=s`draft <b>${t.draft}</b>`;break;case"view":o=s`${t.title?s`<em>${t.title}</em> · `:null}saved ${U(fe(t.version))} by ${t.author??"unknown"}`;break;default:o=s`the built-in view`}return s`<div class="view-source small">
    <${b} name="layout" size=${14} /><span>${o}</span>
    ${a?s`<a href=${S(e.path)}>an older version · show the current one</a>`:null}
    ${r}
    ${t.outdated?.length&&!a?s`<${Js} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||a?null:s`<${Zs} path=${e.path} />
        <${Qs} path=${e.path} view=${t} />`}
  </div>`}function Js(e){let[t,n]=g(null),a=e.outdated.map(o=>o.name).join(", ");return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{await kn(e.path)}catch(o){n(o.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${a} exists; update re-pins this view to it (a new version)`}>
      <${b} name="update" size=${14} /> update ${a}</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function Zs(e){let[t,n]=g(null);return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{Ce.set(await Ye(e.path,null,""))}catch(r){n(r.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${b} name="file-text" size=${14} /> add text</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function Qs(e){let t=qe(e.path),n=Xt(t),[a,r]=g(!1),[o,l]=g(e.view.title??""),[i,c]=g(e.view.finding??""),[u,m]=g(null),[p,v]=g(!1);if(!n&&!a)return null;let y=async C=>{C.preventDefault(),v(!0),m(null);try{let P={charts:t.charts,added:t.added,order:t.order,spans:t.spans};await K("save_view",{path:e.path,prefs:P,title:o,finding:i}),Xe(e.path,()=>({view:{},charts:{},added:[],order:{},spans:{}})),xe(f=>["view","view_history","summary"].includes(f.method)&&f.scope===e.path),r(!1)}catch(P){m(P.message)}finally{v(!1)}};return a?s`<form class="save-form" onSubmit=${y}>
    <${Ie} label="Title"><input value=${o} onInput=${C=>l(C.target.value)} /><//>
    <${Ie} label="Finding"><input value=${i} placeholder="the key result in one sentence"
        onInput=${C=>c(C.target.value)} /><//>
    <div class="save-actions">
      <${ne} type="submit" icon=${p?"hourglass":"save"} disabled=${p}>${p?"Saving\u2026":"Save as view"}<//>
      <${ne} icon="x" kind="quiet" onClick=${()=>r(!1)}>Cancel<//>
      ${u?s`<span class="bad-text small">${u}</span>`:null}
    </div>
  </form>`:s`<${ne} icon="save" class="save-view" onClick=${()=>r(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function cs(e){let t=w(Pn(e.path)),n=t.data?.entries??[],[a,r]=g(null),o=a??n.slice(0,2).map(i=>i.version).reverse(),l=i=>{let c=o.includes(i)?o.filter(u=>u!==i):[...o,i].slice(-2);r(c.sort())};return t.status==="error"?s`<${I} kind="error">${t.error}<//>`:s`<section class="history">
    <h2 class="history-title heading"><${b} name="history" size=${16} /> View history</h2>
    ${t.data&&!n.length?s`<${I}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((i,c)=>s`<li key=${i.version} class=${o.includes(i.version)?"picked":""}>
          <label><input type="checkbox" checked=${o.includes(i.version)} onChange=${()=>l(i.version)} />
            <span class="num muted" data-tip=${i.version}>${U(i.time)}</span>
            <b>${i.title??"untitled"}</b><span class="muted">${i.author??""}</span>
            ${i.message?s`<span>${i.message}</span>`:null}</label>
          <a href=${c===0?S(e.path):S(e.path,{version:i.version})}
            onClick=${u=>{u.preventDefault(),D(c===0?S(e.path):S(e.path,{version:i.version}))}}>${c===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${o.length===2?s`<${ea} path=${e.path} a=${o[0]} b=${o[1]} />`:null}
  </section>`}function ea(e){let t=i=>({method:"view_show",params:{group:e.path,version:i},scope:e.path}),n=w(t(e.a)).data,a=w(t(e.b)).data,r=w(pe(e.path,e.a)).data,o=w(pe(e.path,e.b)).data,l=n&&a?os(rs(n.yaml,a.yaml)):[];return s`<div class="compare">
    <h3 class="block-title heading">Changes from ${U(fe(e.a))} to ${U(fe(e.b))}</h3>
    <pre class="diff code">${l.map(i=>i.kind==="skip"?s`<div class="diff-skip">⋯ ${i.count} unchanged lines</div>`:s`<div class=${`diff-${i.kind}`}>${i.kind==="added"?"+ ":i.kind==="removed"?"\u2212 ":"  "}${i.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${r?.title??e.a}</h3><${rt} path=${e.path} view=${r} plain /></div>
      <div><h3 class="block-title heading">${o?.title??e.b}</h3><${rt} path=${e.path} view=${o} plain /></div>
    </div>
  </div>`}function ds(e){return E(()=>{document.title=`${e.path==="."?"local":e.path} \xB7 Beamtime`},[e.path]),e.history?s`<div class="page"><div class="sections">
      <${z} label=${us(e.path)}><${wt} path=${e.path} /><//>
      <${z} label="history"><${cs} path=${e.path} /><//>
    </div></div>`:s`<div class="page">
    <${ta} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function ta(e){let t=w(pe(e.path,e.version,e.draft));E(()=>{t.status==="ready"&&requestAnimationFrame(It)},[t.status==="ready"]);let n=s`
    <${z} label=${us(e.path)}>
      <${wt} path=${e.path} finding=${t.data?.finding} />
      ${t.data?s`<${ls} path=${e.path} view=${t.data} />`:null}
    <//>
    ${le(e.path.split("/").pop()??"")?null:s`<${qn} path=${e.path} />`}`;return t.status==="error"?s`<div class="sections">${n}
      <${z} label="view">
        ${na(e.path,t.error)?s`<${I} kind="warning">${t.error} The page fills in once the remote answers again.<//>`:s`<${I} kind="error">${t.error}<//>`}
      <//>
    </div>`:s`<${rt} path=${e.path} view=${t.data} before=${n} />`}function us(e){return le(e.split("/").pop()??"")?"run":"group"}function na(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function ms(e){E(()=>{ke(pe(e.id)).then(n=>D(S(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=w(pe(e.id));return t.status==="error"?s`<div class="page"><${I} kind="error">${t.error}<//></div>`:s`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var sa={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},Et=20,Me=-1,aa=[["day",86400],["week",7*86400],["month",30*86400]];function $s(e){let t=R(w(oe()).data).map(i=>i.path),n=w({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),a=w({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});E(()=>{document.title="Timeline \xB7 Beamtime"},[]);let r=Date.now()/1e3,o=R(n.data).filter(i=>i["run.created_at"]).map((i,c)=>({id:i["run.id"],name:i["run.name"]??i["run.id"],group:i["run.group"],status:i["run.status"],start:Date.parse(i["run.created_at"])/1e3,end:i["run.ended_at"]?Date.parse(i["run.ended_at"])/1e3:r,lane:c})),l=(a.data?.entries??[]).map(i=>({id:i.id,type:i.type,group:i.group,description:i.description,t:Date.parse(fe(i.id))/1e3}));return s`<div class="page timeline-page"><div class="sections">
    <${z} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${Ie} label="Group" inline>
          <select value=${e.from} onChange=${i=>D(Ke(i.target.value),{replace:!0})}>
            ${t.map(i=>s`<option value=${i}>${i==="."?"everything":i}</option>`)}
          </select><//>
        <span class="muted small">${o.length} runs · ${l.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${z} label="runs">
      ${n.status==="error"?s`<${I} kind="error">${n.error}<//>`:null}
      ${n.data&&a.data?s`<${ra} bars=${o} marks=${l} />`:s`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function ra(e){let t=re(),n=O(null),a=[...e.bars.flatMap(f=>[f.start,f.end]),...e.marks.map(f=>f.t)],r=a.length?ps(Math.min(...a),Math.max(...a)):ps(Date.now()/1e3-86400,Date.now()/1e3),[o,l]=g(r),i=e.bars.length,c=Math.min(900,Math.max(160,(i+1.5)*Et+40)),m=ln(n,cn,t?(f=>{let k=sn(o[0],o[1]),d=h=>f.colors[sa[h]??"muted"],$=h=>f.colors[h==="verdict"?"good":h==="decision"?"accent":h==="question"?"warn":"muted"];return{style:Kt(f),height:c,x:{range:o,log:!1,format:h=>an(h,k.step),splits:k.at},y:{range:[Me-.8,i+.5],log:!1,reverse:!0,size:150,splits:i<=40?[Me,...e.bars.map(h=>h.lane)]:[Me],format:h=>h===Me?"notes":da(e.bars[Math.round(h)]?.name??"")},draw:({ctx:h,x:A,y:B,px:j,focused:H})=>{let q=Et*.62*j;for(let L of e.bars){let M=A(L.start),x=Math.max(3*j,A(L.end)-M);h.fillStyle=H!==null&&H!==L.id?At(d(L.status),.35):d(L.status),h.beginPath(),h.roundRect(M,B(L.lane)-q/2,x,q,3*j),h.fill()}for(let L of e.marks){let M=A(L.t),x=B(Me),ae=(H===L.id?6:4.5)*j;h.fillStyle=$(L.type),h.beginPath(),h.moveTo(M,x-ae),h.lineTo(M+ae,x),h.lineTo(M,x+ae),h.lineTo(M-ae,x),h.closePath(),h.fill()}},hit:(h,A,B,j)=>{if(Math.abs(A-j(Me))<Et/2){let L=ca(e.marks,M=>Math.abs(B(M.t)-h),8);return L?{key:L.id,rows:ia(L)}:null}let H=Math.round((A-j(0))/(j(1)-j(0))),q=e.bars.find(L=>L.lane===H&&B(L.start)-3<=h&&h<=Math.max(B(L.end),B(L.start)+3)+3);return q?{key:q.id,rows:oa(q)}:null},onClick:h=>{let A=e.marks.find(B=>B.id===h);A?D(S(A.group,{drawer:!0})):D(ce(h))}}})(t):null,[o,e.bars,e.marks],t),p=f=>{if(!m.current)return;f.preventDefault();let k=m.current.xAt(f.clientX),d=Math.exp(f.deltaY*.0015);l(([$,h])=>Ct([k-(k-$)*d,k+(h-k)*d],r))},v=O(null),y=f=>v.current={x:f.clientX,range:o},C=f=>{if(!v.current||!m.current||!(f.buttons&1))return;let k=(f.clientX-v.current.x)*m.current.xPerPixel(),[d,$]=v.current.range;Math.abs(f.clientX-v.current.x)>3&&l(Ct([d-k,$-k],r))},P=Math.max(...a,Date.now()/1e3);return s`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${aa.map(([f,k])=>s`<button type="button" role="radio" aria-checked=${Math.abs(o[1]-o[0]-k)<1}
          onClick=${()=>l(Ct([P-k,P+k*.02],[Math.min(r[0],P-k),r[1]]))}>last ${f}</button>`)}
      <button type="button" role="radio" aria-checked=${o[0]===r[0]&&o[1]===r[1]} onClick=${()=>l(r)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${c}px`}
      onWheel=${p} onPointerDown=${y} onPointerMove=${C} onPointerUp=${()=>v.current=null}></div>
    <p class="muted small">${la(t)}</p>
  </div>`}function oa(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:U(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:Se(e.end-e.start),color:null}]}function ia(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:U(new Date(e.t*1e3).toISOString()),color:null}]}function la(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function ca(e,t,n){let a=null,r=n;for(let o of e){let l=t(o);l<r&&([a,r]=[o,l])}return a}function ps(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function Ct([e,t],n){let a=Math.min(n[1]-n[0],Math.max(60,t-e)),r=Math.max(n[0],Math.min(e,n[1]-a));return[r,r+a]}function da(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function fs(){let e=N(Re),t=O(null);if(E(()=>{let r=t.current;if(!r||!e)return;r.showModal();let o=()=>Re.set(null);return r.addEventListener("close",o),()=>r.removeEventListener("close",o)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},a=String(n.props.title??n.props.y??"Chart");return s`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${a} closedby="any">
    <${X.Provider} value=${e.view}><${se} node=${n} /><//>
  </dialog>`}function hs(e,t){let n=e.toLowerCase(),a=t.toLowerCase();if(!n)return 1;let r=a.indexOf(n);if(r>=0)return 100-Math.min(r,50)-a.length/100;let o=0,l=0;for(let i of a)if(i===n[o]?o++:o>0&&l++,o===n.length)return 40-Math.min(l,39);return 0}function vs(e){let[t,n]=g(e.query),[a,r]=g(0),o=O(null),l=R(w(oe()).data),i=R(w(nt()).data);E(()=>{let d=o.current;d.showModal();let $=()=>Z.set(null);d.addEventListener("close",$);let h=!1,A=H=>{let q=d.getBoundingClientRect();return H.clientX<q.left||H.clientX>q.right||H.clientY<q.top||H.clientY>q.bottom},B=H=>h=A(H),j=H=>h&&A(H)&&d.close();return"closedBy"in HTMLDialogElement.prototype||(d.addEventListener("pointerdown",B),d.addEventListener("pointerup",j)),()=>{d.removeEventListener("close",$),d.removeEventListener("pointerdown",B),d.removeEventListener("pointerup",j)}},[]);let c=()=>o.current?.close(),u=d=>()=>D(d),m=V.value,p=m.page==="group"?m.path:".",v=(d,$,h,A)=>({section:"Commands",label:d,detail:$,sym:{icon:h,tone:"muted",label:d},run:A}),C=[...l.map(d=>({section:"Groups",label:d.path==="."?"local":d.path,detail:`${d.runs} runs${d.proposal?` \xB7 ${d.proposal}`:""}`,sym:T("research",d.status),run:u(S(d.path))})),...i.map(d=>({section:"Runs",label:d["run.name"]??d["run.id"],detail:`${d["run.status"]} \xB7 ${d["run.path"]}`,sym:T("run",d["run.status"]),run:u(S(d["run.path"]))})),v("Theme: light","","sun",()=>Fe("light")),v("Theme: dark","","moon",()=>Fe("dark")),v("Theme: follow the system","","monitor",()=>Fe("system")),v("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),v("Show notes and timeline","i","file-text",u(S(p,{drawer:!0}))),v("Show or hide the sidebar","\u2318B","panel-left",()=>J.set(!J.value)),v(ee.value?"Resume live updates":"Pause live updates","p",ee.value?"play":"pause",()=>ee.set(!ee.value)),v("Keyboard shortcuts","?","keyboard",()=>me.set(!0)),v("Settings","","settings",u("/settings/appearance"))].map(d=>({it:d,s:Math.max(hs(t,d.label),hs(t,d.detail)*.5)})).filter(d=>d.s>0).sort((d,$)=>$.s-d.s||gs(d.it.section)-gs($.it.section)).slice(0,60).map(d=>d.it),P=d=>{d&&(c(),d.run())},f=d=>{if(d.key==="ArrowDown")r(Math.min(C.length-1,a+1));else if(d.key==="ArrowUp")r(Math.max(0,a-1));else if(d.key==="Enter")P(C[a]);else return;d.preventDefault()},k="";return s`<dialog class="sheet" ref=${o} aria-label="Search" closedby="any">
    <div class="palette-input"><${b} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${C[a]?`pal-${a}`:void 0}
        onInput=${d=>{n(d.target.value),r(0)}} onKeyDown=${f} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${C.map((d,$)=>{let h=d.section!==k&&!t?k=d.section:null;return s`${h?s`<li class="palette-head small" role="presentation">${h}</li>`:null}
          <li id=${`pal-${$}`} class="item" role="option" aria-selected=${$===a}
              onMouseMove=${()=>r($)} onClick=${()=>P(d)}>
            <${_} spec=${d.sym} /><span class="label">${d.label}</span><span class="detail small">${d.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function gs(e){return["Groups","Runs","Commands"].indexOf(e)}function ot(e,t=[]){let n=new Map,a=(o,l={})=>({path:o,name:o==="."?"local":o.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let o of e)n.set(o.path,a(o.path,o));n.has(".")||n.set(".",a("."));for(let o of t)o.name!=="local"&&(n.has(o.name)||n.set(o.name,a(o.name)),Object.assign(n.get(o.name),{state:o.state,error:o.error}));for(let o of n.values()){if(W(o.path))continue;let l=o.path.lastIndexOf("/"),i=l<0?".":o.path.slice(0,l);(n.get(i)??n.get(ve(o.path))??n.get(".")).children.push(o)}for(let o of n.values())o.children.sort((l,i)=>l.name.localeCompare(i.name));let r=[...n.values()].filter(o=>o.path!=="."&&W(o.path)).sort((o,l)=>o.name.localeCompare(l.name));return[n.get("."),...r]}function bs(e,t,n,a=new Set){let r=[],o=n.toLowerCase(),l=i=>{(!o||i.path.toLowerCase().includes(o)||ys(i,o))&&(r.push(i),(o||(W(i.path)?!a.has(i.path):t.has(i.path)))&&i.children.forEach(l))};return e.forEach(l),r}function ys(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||ys(n,t))}function ws(e,t){if(W(t))return e;let n=t.lastIndexOf("/"),a=n<0?".":t.slice(0,n),r=o=>o.path===a?o:o.children.map(r).find(l=>l)??null;return e.map(r).find(o=>o)?.children??[]}function ks(e){return W(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function xs(){let e=N(V),t=w(oe()),[n,a]=g(()=>new Set(ye("open",[]))),[r,o]=g(()=>new Set(ye("closed-hosts",[]))),[l,i]=g(""),c=O(null),u=e.page==="group"?e.path:null,m=ot(R(t.data),t.data?.meta?.sources??[]),p=bs(m,pa(n,u),l,r),v=f=>W(f)?!r.has(f):n.has(f),y=(f,k)=>{let d=k??!v(f);if(W(f)){let h=new Set(r);d?h.delete(f):h.add(f),we("closed-hosts",[...h]),o(h);return}let $=new Set(n);d?$.add(f):$.delete(f),we("open",[...$]),a($)},C=O(u);return E(()=>{u!==C.current&&u&&!W(u)&&r.has(ve(u))&&y(ve(u),!0),C.current=u},[u]),s`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${b} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${l} aria-label="Filter groups"
        onInput=${f=>i(f.target.value)} />
    </label>
    <div class="tree" ref=${c} onKeyDown=${f=>{let k=[...c.current?.querySelectorAll("a.tree-item")??[]],d=k.indexOf(document.activeElement),$=p[d];switch(f.key){case"ArrowDown":k[Math.min(k.length-1,d+1)]?.focus();break;case"ArrowUp":k[Math.max(0,d-1)]?.focus();break;case"ArrowRight":$?.children.length&&y($.path,!0);break;case"ArrowLeft":$?.children.length&&v($.path)?y($.path,!1):$&&k[p.findIndex(h=>h.path===ma($.path))]?.focus();break;default:return}f.preventDefault()}} role="tree">
      ${p.map(f=>s`<${ua} key=${f.path} node=${f} current=${f.path===u}
        open=${v(f.path)||!!l} onToggle=${()=>y(f.path)} />`)}
    </div>
  </nav>`}function ua(e){let t=e.node,n=()=>He(t.path),a=t.children.length>0,r=t.state==="unreachable";return s`<a class=${`tree-item${e.current?" current":""}${t.path.startsWith("@")&&W(t.path)?" source-root":""}`} href=${S(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${a?e.open:void 0}
      style=${`padding-inline-start:${8+ks(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${o=>{o.metaKey||o.ctrlKey||(o.preventDefault(),D(S(t.path)))}}>
    <span class="twisty" onClick=${o=>{o.preventDefault(),o.stopPropagation(),e.onToggle()}}>
      ${a?s`<${b} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    ${W(t.path)?s`<${_} size=${14} spec=${{icon:r?"cloud-off":"server",tone:"muted",label:r?`Unreachable: ${t.error??"no answer"}`:t.path==="."?"This machine":`Remote host ${t.name}`}} />`:null}
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?s`<${_} spec=${T("run","running")} size=${14} />`:null}
      ${t.failed?s`<${_} spec=${{...T("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function ma(e){if(W(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function pa(e,t){if(!t||t===".")return e;let n=new Set(e),a=t.split("/");for(let r=1;r<a.length;r++)n.add(a.slice(0,r).join("/"));return n}function Es(){let e=N(V),t=N(J),n=N(Z),a=N(me),r=O(null);E(()=>Ot(()=>r.current),[]),E(()=>(addEventListener("keydown",Ss),()=>removeEventListener("keydown",Ss)),[]);let o=e.page==="group"&&e.drawer,l;switch(e.page){case"group":l=s`<${ds} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":l=s`<${ms} id=${e.id} />`;break;case"settings":l=s`<${Tn} />`;break;case"timeline":l=s`<${$s} key=${e.from} from=${e.from} />`;break;default:l=s`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return de||!1?s`<main class="main render-main" ref=${r}>${l}</main>`:s`<div class=${`shell${t?"":" no-sidebar"}${o?" with-drawer":""}`}>
    <${In} />
    ${t?s`<${xs} />`:null}
    <main class="main" ref=${r}>${l}</main>
    ${o?s`<${Vn} path=${e.path} run=${e.run} />`:null}
    <${zn} />
    ${n!==null?s`<${vs} query=${n} />`:null}
    ${a?s`<${fa} />`:null}
    <${fs} />
  </div>`}function Ss(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),Z.set(Z.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),J.set(!J.value);return}if(e.key==="Escape"){if(Z.value!==null||me.value)return;let a=V.value;return a.page==="group"&&a.run?D(S(a.path,{drawer:!0}),{replace:!0}):a.page==="group"&&a.drawer?D(S(a.path),{replace:!0}):void 0}if(t||e.altKey||En(e)||Z.value!==null||me.value)return;let n=V.value;switch(e.key){case"/":e.preventDefault(),Z.set("");break;case"?":me.set(!me.value);break;case"p":ee.set(!ee.value);break;case"i":n.page==="group"&&D(S(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":J.set(!J.value);break;case"[":case"]":n.page==="group"&&$a(n.path,e.key==="]"?1:-1);break}}async function $a(e,t){let n=await ke(oe()),a=ws(ot(R(n),n?.meta?.sources??[]),e),r=a.findIndex(l=>l.path===e),o=a[r+t];o&&D(S(o.path))}function fa(){let e=O(null);return E(()=>{let t=e.current;t.showModal();let n=()=>me.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),s`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${Je.map(([t,n])=>s`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${ne} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}zt();if(de){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(ue.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>De.n,Bt&&Wt()}hn();var ha=K("meta").then(e=>(de&&(e={...e,settings:{...e.settings,theme_mode:ue.value}}),Ze(e),e));!de&&!!1&&Pt(async()=>{let[e,t]=await Promise.all([ha,K("meta")]);e.bundle!==t.bundle?location.reload():Ze(t)});Tt(s`<${Es} />`,document.getElementById("app"));
