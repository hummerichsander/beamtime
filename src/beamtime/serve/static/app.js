import{$ as re,$a as on,A as Dt,B as Nt,C as xe,Ca as je,D as le,Da as T,E as S,Ea as ct,F as He,Fa as jt,G as ce,Ga as dt,H as _e,Ha as We,I as ve,Ia as Ge,J as j,Ja as Wt,K as G,Ka as Gt,L as _t,La as Vt,Ma as qt,N,Na as Xt,O as Rt,P as Lt,Q as de,Qa as Yt,R as Re,Ra as Jt,S as Pt,Sa as Zt,T as Ae,Ta as Qt,U as rt,Ua as en,V as ue,Va as tn,W as Bt,Wa as nn,X as ot,Xa as sn,Y as Ke,Z as q,Za as an,_ as ae,_a as rn,aa as Ue,ab as ln,ba as Ht,bb as cn,c as xt,ca as Le,cb as dn,d as s,da as Pe,db as un,e as g,eb as mn,f as E,fa as At,g as St,ga as Kt,h as O,ha as v,i as De,ia as _,j as ie,ja as Fe,ka as ee,la as I,m as ge,ma as L,n as D,na as it,o as ye,oa as W,p as we,pa as Ut,qa as z,ra as te,s as K,sa as Oe,t as Ne,ta as lt,u as ke,ua as Ft,v as at,va as X,w as k,wa as fe,x as Tt,xa as be,y as Q,ya as Se,z as Mt,za as U}from"./chunks/chunk-6NWOLH2I.js";import{a as Et,b as Ct}from"./chunks/chunk-O2K4N3UR.js";import{e as Ot,i as It,j as zt}from"./chunks/chunk-CHIPVRI3.js";import"./chunks/chunk-VC46IEJQ.js";function Ee(e,t){xe(n=>t.includes(n.method)&&n.scope!==null&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var ut=["notes","timeline","groups","check","card","memory_show","status"];async function mt(e,t){let n=e.meta??{};await K("note_add",{group:e.group,type:e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),Ee(e.group,ut)}async function pn(e,t,n,a){await K("note_add",{group:e,type:t,description:n,body:a}),Ee(e,ut)}async function $n(e,t){await K("memory_update",{group:e,body:t}),Ee(e,["memory_show","status"])}async function fn(e,t){let n=await K("proposal_show",{group:e}),a=Object.fromEntries(Object.entries(n.proposal??{}).filter(([r])=>!["schema","author","user","supersedes"].includes(r)));await K("proposal_set",{group:e,proposal:{...a,statement:t}}),Ee(e,["groups","proposal_show","check","summary"])}async function hn(e){await K("note_rm",{note:e.id}),Ee(e.group,ut)}async function gn(e,t,n){await K("name",{run:e,name:n}),Ee(t,["card","runs","groups","summary","series"])}async function Ve(e,t,n){let a=await K("view_text",{path:e,id:t,text:n});return xe(r=>["view","view_history"].includes(r.method)&&r.scope===e),a.id}async function vn(e){await K("view_upgrade",{group:e}),xe(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var Ce=new ge(null);async function bn(e,t){return await K("set",{key:e,value:t}),K("meta")}var Y=new ge(ye("sidebar",!0)),J=new ge(null),me=new ge(!1),Te=new ge(null);Y.subscribe(e=>we("sidebar",e));var yn=ye("visit",Date.now());we("visit",Date.now());function wn(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var qe=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var ws=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function Xe(e){Te.set(e),Ae.set(e.theme),e.settings?.theme_mode&&ue.set(e.settings.theme_mode),ot()}var kn=0;async function pt(e,t){let n=++kn;e==="theme_mode"&&(ue.set(t),ot());let a=await bn(e,t);n===kn&&Xe(a)}function xn(){let e=D(ue),t=re(),n=D(Te),[a,r]=g(null);E(()=>{document.title="Settings \xB7 Beamtime"},[]);let o=(c,m)=>{r(null),pt(c,m).catch(u=>r(u.message))},l=n?.settings??{},i=(c,m,u)=>s`
    <label class="field-label small" for=${`setting-${c}`}>${m}</label>
    <span class="input body">
      <select id=${`setting-${c}`} value=${l[c]} onChange=${p=>o(c,p.target.value)}>
        ${u.map(p=>s`<option value=${p}>${p}</option>`)}
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
          ${ws.map(([c,m,u])=>s`<button type="button" role="radio" aria-checked=${e===c} onClick=${()=>o("theme_mode",c)}>
            <${v} name=${m} size=${15} />${u}</button>`)}
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
        ${(n?.figure_styles??[]).length?s`<${je} options=${n.figure_styles} value=${l.figure_style??[]} label="Style sheets"
              placeholder="Add a style" onChange=${c=>o("figure_style",c)} />`:s`<span class="muted small"><code>${JSON.stringify(l.figure_style??[])}</code>; choosing others needs the figures
              extra: <code>uv add matplotlib scienceplots</code></span>`}
      </div>
      <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(l.figure_style??[])})</code>, in this order
        (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
        <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <//>
    <${z} label="keyboard">
      <table class="kv">${qe.map(([c,m])=>s`<tr><td><kbd class="small">${c}</kbd></td><td>${m}</td></tr>`)}</table>
    <//>
    <${z} label="about">
      <table class="kv">
        <tr><td class="muted">version</td><td>${n?.version}</td></tr>
        <tr><td class="muted">root</td><td><code class="code">${n?.root}</code></td></tr>
        <tr><td class="muted">log dir</td><td><code class="code">${n?.logdir}</code></td></tr>
      </table>
    <//>
  </div></div>`}var oe=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),pe=(e,t=null,n=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{}},scope:e}),$t=e=>({method:"summary",params:{path:e},scope:e}),Ye=e=>({method:"groups",params:{from:e,depth:0},scope:e}),Sn=e=>({method:"check",params:{group:e},scope:e}),En=e=>({method:"proposal_show",params:{group:e},scope:e}),Je=(e,t)=>({method:"card",params:{run:_e(e,t)},scope:t}),Cn=(e,t)=>({method:"output",params:{run:_e(e,t),tail:30},scope:t}),Ie=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),Ze=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),Tn=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),Mn=()=>({method:"status",params:{},scope:"."}),Qe=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function ze(e){for(let t of[pe(e),Ye(e),Ie(e),$t(e)])at(t);ke(pe(e)).then(t=>{for(let n of Dn(t.view))at(n)}).catch(()=>{})}function Dn(e){return e?[...ks.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(Dn)]:[]}var ks=new Set(["line","custom"]),Nn=e=>({method:"view_history",params:{group:e},scope:e});var _n={system:"light",light:"dark",dark:"system"},xs={system:"monitor",light:"sun",dark:"moon"};function Rn(){let e=D(Te),t=D(ue),n=D(Y);return s`<header class="topbar">
    <${W} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>Y.set(!n)} />
    <a class="project heading" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>J.set("")} aria-label="Search (⌘K)">
      <${v} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${Ss} />
      <${W} icon=${xs[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${_n[t]})`}
        onClick=${()=>{pt("theme_mode",_n[t])}} />
      <a class="icon-button" href=${He(G.value.page==="group"?G.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${v} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${v} name="settings" size=${16} /></a>
    </div>
  </header>`}function Ss(){let t=(k(oe()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?s`${[{name:"local",state:"connected"},...t].map(n=>s`<a class=${`source small ${n.state}`}
      href=${S(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${v} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:s`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${v} name="server" size=${15} /> local</span>`}function Es(e){let[t,n]=g(Date.now());return E(()=>{let a=setInterval(()=>n(Date.now()),e);return()=>clearInterval(a)},[e]),t}function Cs(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function Ln(){let e=D(Mt),t=D(Q),n=D(Dt),a=D(G),r=Es(5e3),o=k(Mn()).data,l=L(k(Qe()).data),i=D(Te),c=o?.daemon,m=o?.runs?.running??0,u=l.filter(P=>P["run.status"]==="failed"&&Cs(P["run.ended_at"])>yn).length,p=o?.meta?.freshness,[y,b,C]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&c?["",`live \xB7 updated ${U(new Date(n).toISOString(),r)}`,`beamtime serve, pid ${c.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return s`<footer class="statusbar small">
    <span class="status-item" data-tip=${C}><span class=${`live-dot ${y}`}></span>${b}</span>
    ${m?s`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>J.set("running")}>
          <${v} name="circle-dot" size=${14} class="tone-accent" />${m} running</button>`:null}
    ${u?s`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>J.set("failed")}>
          <${v} name="circle-x" size=${14} />${u} failed since your last visit</button>`:null}
    ${p?.behind?s`<span class="status-item warn-text" data-tip=${p.text}><${v} name="hourglass" size=${14} />${p.behind} runs behind</span>`:null}
    ${p?.damaged?.length?s`<span class="status-item warn-text" data-tip=${p.damaged.join(`
`)}><${v} name="triangle-alert" size=${14} />${p.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${a.page==="group"&&a.run?s`<span class="status-item"><${v} name="activity" size=${14} />1 run selected</span>`:null}
    <${W} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>Q.set(!t)} />
    ${i?.outdated?s`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item">${i?.version?`beamtime ${i.version}`:""}</span>
  </footer>`}var Pn=null;function et(e){let t=O(null),[n,a]=g(null),[r,o]=g(!1),[l,i]=g(!1);E(()=>{let p=!0;return Pn??=import("./chunks/md-SW3VT2BQ.js"),Pn.then(y=>y.render(e.text??"")).then(y=>p&&a(y)),()=>{p=!1}},[e.text]),St(()=>{let p=t.current;if(!p||!e.clamp)return;let y=()=>i(p.scrollHeight>p.clientHeight+2),b=new ResizeObserver(y);return b.observe(p),()=>b.disconnect()},[e.clamp,n]);let c=e.clamp&&!r,m=`md${c?" clamped":""}`,u=c?`--clamp:${e.clamp}`:"";return s`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?s`<div class=${m} ref=${t} style=${u}>
          ${(e.text??"").split(/\n{2,}/).map(p=>s`<p>${p}</p>`)}
        </div>`:s`<div class=${m} ref=${t} style=${u} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(l||r)?s`<button type="button" class="link small more" onClick=${()=>o(!r)}>${r?"less":"more"}</button>`:null}
  </div>`}function he(e){let[t,n]=g(!!e.startEditing),[a,r]=g(e.value),[o,l]=g(null),[i,c]=g(null),m=O(null),u=O(!1);E(()=>l(null),[e.value]),E(()=>{!t||!m.current||(m.current.focus(),e.startEditing?m.current.select():m.current.setSelectionRange(m.current.value.length,m.current.value.length))},[t]);let[p,y]=g(!1),b=e.locked??void 0,C=$=>{if(!$.target.closest("a, button, input, summary")){if(b)return y(!0);$.preventDefault(),r(o??e.value),c(null),u.current=!1,n(!0)}},P=()=>{u.current=!0,n(!1),c(null),e.onCancel?.()},f=async()=>{if(u.current)return;u.current=!0;let $=e.multiline?a.trim():a.replace(/\s*\n\s*/g," ").trim();if($===e.value.trim()||!$&&!e.multiline)return P();n(!1),l($);try{await e.onSave($)}catch(h){l(null),r($),c(h.message),u.current=!1,n(!0)}},w=$=>{if($.key==="Escape")return $.preventDefault(),$.stopPropagation(),P();$.key!=="Enter"||$.isComposing||$.keyCode===229||(!e.multiline||$.metaKey||$.ctrlKey)&&($.preventDefault(),f())};if(t)return s`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${m} class="edit-field" value=${a} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,a.split(`
`).length+1)):1}
        onInput=${$=>r($.target.value)} onKeyDown=${w} onBlur=${f}></textarea>
      <span class="edit-hint small">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${i?s` · <span class="bad-text">${i}</span>`:null}</span>
    </div>`;let d=o??e.value;return s`<div class=${`editable${b?" locked":""}${o!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${b?`${e.label}: ${b}`:`Edit ${e.label}`}
      data-tip=${b} onClick=${C} onBlur=${()=>y(!1)}
      onKeyDown=${$=>$.key==="Enter"&&$.target===$.currentTarget&&C($)}>
    ${d.trim()?e.render?e.render(d):d:s`<span class="muted">${e.placeholder??"Click to write"}</span>`}
    ${p&&b?s`<span class="edit-hint small locked-why" role="status"><${v} name="lock" size=${14} /> ${b}</span>`:null}
  </div>`}function ft(e){let t=[];if(e.effect!==void 0&&e.effect!==null){let n=e.ci?` [${X(e.ci[0])}, ${X(e.ci[1])}]`:"";t.push(`${e.effect>=0?"+":""}${X(e.effect)}${n}`)}return e.threshold!==void 0&&e.threshold!==null&&t.push(`needs ${e.op} ${X(e.threshold)}`),e.points&&t.push(`${e.points} point${e.points>1?"s":""}`),e.detail&&t.push(e.detail),t.join(" \xB7 ")}function ht(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function On({node:e}){let t=ae("proposal"),n=ae("check"),a=t.data,r=n.data;if(!a)return s`<${ee} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let o=a.proposal??{},l=(a.versions??[]).filter(c=>c.version!==a.version),i=!e.props.of||e.props.of===".";return s`<${ee} title="Predictions" result=${t} class="proposal">
    ${i?null:s`<p class="statement">${o.statement}</p>`}
    ${o.rationale?s`<p class="rationale prose">${o.rationale}</p>`:null}
    <div class="predictions">
      ${(r?.predictions??[]).map(c=>s`<div class="prediction" key=${c.name}>
          <${_} spec=${T("result",c.result)} />
          <span class="pname">${c.name}</span>
          <span class="pdetail num small">${ft(c)}</span>
        </div>`)}
    </div>
    ${l.length?s`<${lt} summary=${`${l.length} earlier version${l.length>1?"s":""}`}>
          ${l.map(c=>s`<p class="small"><code>${c.version}</code> ${c.statement}
            <span class="muted">(${c.runs} runs, check ${c.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function In({node:e}){let t=ae("main"),n=e.data?.main.params.group??".",a=t.data?.chain??[],r=a.find(i=>i.group===n)??null,o=a.filter(i=>i.group!==n),l=r?.notes_since?"out of date":r?`version ${r.versions??1}`:"none yet";return s`<${it} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?l:void 0} open=${!1} result=${t}
      action=${s`<${_} spec=${{icon:"circle-help",tone:"muted",label:Ms}} />`}>
    <${he} value=${r?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${i=>s`<${et} text=${i} />`} onSave=${i=>$n(n,i)} />
    ${r&&(r.body?.length>(t.data?.budget??1/0)||r.notes_since>=Ts)?s`<p class="memory-meta small warn-text">${r.body?.length>t.data.budget?`${r.body.length} characters, beyond the budget of ${t.data.budget}`:`${r.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${r?s`<p class="memory-meta small">${r.author} · covers notes until ${r.covers_until?.slice(0,10)}
          ${r.notes_since?s` · <span class="warn-text">${r.notes_since} newer note${r.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${o.length?s`<p class="memory-meta small">Memory above this group: ${o.map((i,c)=>s`${c?", ":""}<a href=${S(i.group)}>${i.group==="."?"local":i.group}</a>`)}</p>`:null}
  <//>`}var Ts=5,Ms="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",Ds="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function zn({node:e}){let t=ae("main"),n=e.data?.main.params.from??".",a=L(t.data).filter(r=>r.path!==n);return s`<${ee} title=${e.props.title} count=${t.data?String(a.length):void 0} result=${t}>
    ${t.data&&!a.length?s`<${I}>No groups below.<//>`:null}
    <div class="group-list">
      ${a.map(r=>{let[o,l]=ht(r.progress),i=(r.failed??0)+(r.killed??0)+(r.lost??0);return s`<a class="group-row" key=${r.path} href=${S(r.path)}
            onPointerEnter=${()=>ze(r.path)} onFocus=${()=>ze(r.path)}>
          <${_} spec=${T("research",r.status)} />
          <span class="gname heading">${r.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${r.status!=="concluded"?s`<span class=${`tone-${T("research",r.status).tone}`}>${T("research",r.status).label}</span>`:null}
            ${r.check?s`<${_} spec=${T("result",r.check)} word />`:null}
            ${r.verdict?s`<${_} spec=${T("verdict",r.verdict)} />`:null}
            ${o?s`<span data-tip=${l}>${o}</span>`:null}
            <span class="num"><b>${r.runs}</b> runs</span>
            ${r.running?s`<${_} spec=${T("run","running")} />`:null}
            ${i?s`<span class="tone-bad num" data-tip="failed, killed or lost"><${v} name="circle-x" size=${14} /> ${i}</span>`:null}
          </span>
          ${r.proposal?s`<span class="gstatement caption">${r.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function Bn({node:e}){let t=ae("main"),n=e.data?.main.params.from??".",[a,r]=g(!1),o=(t.data?.entries??[]).filter(i=>!String(i.state??"").startsWith("superseded")),l=t.data?.meta?.matched??o.length;return s`<${it} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(l):void 0} result=${t}
      action=${s`<${_} spec=${{icon:"circle-help",tone:"muted",label:Ds}} />
        ${s`<${W} icon="plus" label="Add a note" onClick=${()=>r(!0)} />`}`}>
    <div class="notes">
      ${a?s`<${Rs} group=${n} onDone=${()=>r(!1)} />`:null}
      ${t.data&&!o.length&&!a?s`<p class="muted small">No notes yet.</p>`:null}
      ${o.map(i=>s`<${tt} key=${i.id} note=${i} scope=${n} />`)}
      ${t.data?.more&&e.data?s`<${Hn} call=${e.data.main} before=${o[o.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var Ns=20;function Hn(e){let[t,n]=g(!1),a=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:Ns}}:null,r=k(a);if(!t)return s`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(r.status==="error")return s`<p class="bad-text small">${r.error}</p>`;let o=r.data?.entries??[];return s`${r.data?null:s`<div class="skeleton" style="block-size: 40px"></div>`}
    ${o.map(l=>s`<${tt} key=${l.id} note=${l} scope=${e.scope} />`)}
    ${r.data?.more?s`<${Hn} call=${e.call} before=${o[o.length-1]?.id} scope=${e.scope} />`:null}`}var _s=["observation","idea","question","decision"];function Rs(e){let[t,n]=g("observation"),[a,r]=g(""),[o,l]=g(""),[i,c]=g(null),[m,u]=g(!1),p=async b=>{if(b.preventDefault(),!a.trim())return c("give the note a title");u(!0);try{await pn(e.group,t,a.trim(),o.trim()),e.onDone()}catch(C){c(C.message),u(!1)}};return s`<form class="note new-note" onSubmit=${p} onKeyDown=${b=>{b.key==="Escape"&&e.onDone(),b.key==="Enter"&&(b.metaKey||b.ctrlKey)&&p(b)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${t} aria-label="Note type" onChange=${b=>n(b.target.value)}>
        ${_s.map(b=>s`<option value=${b}>${b}</option>`)}
      </select></span>
      <span class="input body new-note-field"><input class="new-note-title" value=${a} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${b=>r(b.target.value)} /></span>
    </div>
    <span class="input small"><textarea class="new-note-body" rows="4" value=${o} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${b=>l(b.target.value)}></textarea></span>
    <div class="save-actions">
      <${te} type="submit" icon=${m?"hourglass":"plus"} disabled=${m}>${m?"Adding\u2026":"Add note"}<//>
      <${te} icon="x" kind="quiet" onClick=${e.onDone}>Cancel<//>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${i?s`<span class="bad-text small">${i}</span>`:null}
    </div>
  </form>`}function tt(e){let t=e.note,[n,a]=g(!!e.open),[r,o]=g(!1),l=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,i=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),c=t.meta?.author;return s`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${m=>!m.target.closest(".editable, a, .note-delete")&&a(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${v} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${_} spec=${T("note",t.type)} />
      <${he} value=${t.description} label="the note's title" class="note-title heading" render=${Ps}
        onSave=${m=>mt(t,{description:m})} />
      ${t.overall?s`<${_} spec=${T("verdict",t.overall)} />`:null}
      ${t.state?s`<${Ut} tone="warn">${t.state}<//>`:null}
      ${l?s`<a class="note-group small" href=${S(l)} data-tip="from this group">${Ls(l,e.scope)}</a>`:null}
      <span class="note-meta small">${c?`${c} \xB7 `:""}${U(i)}</span>
      ${s`<${W} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${r}
        onClick=${m=>{m.stopPropagation(),o(!r)}} />`}
    </div>
    ${r?s`<div class="note-confirm small" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <${te} icon="trash" kind="danger" onClick=${()=>{hn(t)}}>Delete<//>
          <${te} icon="x" kind="quiet" onClick=${()=>o(!1)}>Cancel<//>
        </div>`:null}
    ${n?s`<${he} value=${t.body??""} label="the note" multiline class="note-body prose markdown"
          placeholder="Add details in Markdown" render=${m=>s`<${et} text=${m} />`}
          onSave=${m=>mt(t,{body:m})} />`:null}
  </article>`}function Ls(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,a=n.split("/").pop()??n;return le(a)?a.slice(-8):n}function An({node:e}){let t=ae("main"),n=t.data?.lines??[],a=t.data?.meta??{},r=s`<${v} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${a.total_lines??n.length} lines${(a.shown??0)<(a.total_lines??0)?`, last ${a.shown}`:""}`:""}</span>`;return s`<${ee} result=${t}>
    <${lt} summary=${r} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function Kn({node:e}){let t=ie(q);return s`<${ee} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${he} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${Ce.value===e.id} onCancel=${()=>Ce.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>s`<${et} text=${n} />`}
      onSave=${n=>(Ce.set(null),Ve(t.path,e.id,n))} />
  <//>`}function Un({node:e}){return s`<${I} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function Ps(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let a=n.slice(2,-2),[r]=a.split(/[#@]/),o=r.split("/").pop()??"";return s`<a href=${le(o)?ce(o):S(r)}>${a}</a>`}return n.startsWith("`")?s`<code>${n.slice(1,-1)}</code>`:n})}function Fn(e){let t=()=>N(S(e.path),{replace:!0});return s`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${v} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${W} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?s`<${Os} id=${e.run} scope=${e.path} />`:s`<${Is} path=${e.path} />`}
  </aside>`}function Os({id:e,scope:t}){let n=k(Je(e,t)).data,a=k(Cn(e,t)).data,r=k(Ie(t)).data,o=re(),l=De(()=>Ue(L(r).map(u=>u["run.id"]),o).get(e),[r,o,e]);if(!n)return s`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let i=n.run,c=Object.entries(n.metrics??{}),m=Ot(l,o);return s`<div class="drawer-body">
    <h3 class="heading"><span class=${m.class} style=${m.style}></span>
      <a href=${ce(e)}>${i.name}</a></h3>
    <p class="facts small">
      <${_} spec=${T("run",i.status)} word />
      <span><b>${be(i.steps)}</b> steps</span>
      <span><b>${Se(i.duration_s)}</b></span>
      <span data-tip=${i.created_at}>${U(i.created_at)}</span>
    </p>
    ${i.error?s`<pre class="log code bad-text">${i.error}</pre>`:null}
    <h4 class="small">Config</h4>
    <table class="kv small">${Object.entries(n.config??{}).map(([u,p])=>s`<tr><td>${u}</td><td class="num">${X(p)}</td></tr>`)}</table>
    ${c.length?s`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${c.map(([u,p])=>s`<tr><td>${u}</td><td class="num"><b>${X(p.last)}</b></td>
              <td class="num">${X(p.min)}</td><td class="num">${X(p.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?s`<h4 class="small">Cited by</h4>${n.cited_by.map(u=>s`<p class="small"><${_} spec=${T("note",u.type)} /> ${u.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(u=>s`<div class="event small"><span class="muted num">${u.t?.slice(5,16).replace("T"," ")}</span>
        <${v} name=${ct(u.type)} size=${14} /><span>${u.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(a?.lines??[]).join(`
`)}</pre>
  </div>`}function Is({path:e}){let t=k(Ze(e)).data,n=k(Tn(e)).data;return s`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?s`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(a=>!String(a.state??"").startsWith("superseded")).map(a=>s`<${tt} key=${a.id} note=${a} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(a=>s`<div class="event small"><span class="muted num">${a.t?.slice(5,16).replace("T"," ")}</span>
        <${v} name=${a.kind==="note"?"file-text":ct(a.type)} size=${14} />
        <span>${a.run?s`<a href=${ce(a.run)}>${a.run.slice(-8)}</a> `:null}${a.description??a.type}</span></div>`)}
  </div>`}var gt=["failed","killed","lost"];function vt(e){let t=ve(e.path),n=t==="."?e.path:e.path.slice(t.length+1),a=j(e.path)?[]:n.split("/"),r=a.length&&le(a[a.length-1])?a[a.length-1]:null,o=a.slice(0,-1),l=i=>[...t==="."?[]:[t],...o.slice(0,i+1)].join("/");return s`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${a.length?s`<a href=${S(t)}>${t==="."?"local":t}</a>`:null}
      ${o.map((i,c)=>s`<span>/</span><a href=${S(l(c))}>${i}</a>`)}
    </nav>
    ${r?s`<${Hs} id=${r} scope=${e.path} />`:s`<${zs} path=${e.path} />`}
    ${e.finding?s`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function zs({path:e}){let t=L(k(Ye(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return s`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=gt.reduce((r,o)=>r+(t[o]??0),0);return s`
    <h1 class="page-title title" tabindex="-1">${n} <${_} spec=${T("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?s`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?s`<span><b>${t.finished}</b> finished</span>`:null}
      ${a?s`<span class="tone-bad" data-tip=${gt.filter(r=>t[r]).map(r=>`${t[r]} ${r}`).join(", ")}>
            <${v} name="circle-x" size=${15} /> <b>${a}</b> ${a===1?gt.find(r=>t[r]):"ended early"}</span>`:null}
      ${t.notes?s`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${Wn} path=${e} />
    </p>`}function jn({path:e}){let t=L(k(Ye(e)).data)[0]??null,n=k(t?.proposal?Sn(e):null).data,a=k(t?.proposal?En(e):null).data;if(!t?.proposal)return null;let r=a?.proposal?.rationale,o=a?.versions?.find(c=>c.version===a.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[l,i]=ht(n?.progress?.text??t.progress);return s`<${z} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${he} value=${t.proposal} label="the proposal's statement" locked=${a?o:"Loading the proposal\u2026"}
          render=${c=>s`<span data-tip=${o?void 0:r}>${c}</span>`}
          onSave=${c=>fn(e,c)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(c=>{let m=T("result",c.result),u=ft(c),p=u?`${m.label}: ${u}`:m.label;return s`<span class=${`check small tone-${m.tone}`} key=${c.name} data-tip=${p}
              aria-label=${`${c.name}: ${p}`} tabindex="0"><${v} name=${m.icon} size=${14} />${c.name}</span>`})}
        ${n?.provisional||l?s`<span class="small">
              ${n?.provisional?s`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${l?s`<span class="muted" data-tip=${i}>${n?.provisional?" \xB7 ":""}${l}</span>`:null}
            </span>`:null}
      </div>
      <${Bs} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function Bs(e){let t=k(e.verdict?Ze(e.path):null).data;if(!e.verdict)return s`<p class="verdict-line muted">no verdict yet</p>`;let n=T("verdict",e.verdict),a=(t?.entries??[]).find(o=>o.type==="verdict"&&(o.group??e.path)===e.path),r=a?fe(a.id):null;return s`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${v} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${a?s`<span class="small muted" data-tip=${r}>verdict${a.meta?.author?` by ${a.meta.author}`:""}${r?` \xB7 ${U(r)}`:""}</span>`:null}
  </p>`}function Hs({id:e,scope:t}){let n=k(Je(e,t)).data;if(!n)return s`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=n.run,r=()=>{navigator.clipboard?.writeText(a.id)};return s`
    <h1 class="page-title title" tabindex="-1"><${he} value=${a.name??a.id} label="the run's name" class="title-edit"
        onSave=${o=>gn(a.id,t,o.trim())} />
      <${_} spec=${T("run",a.status)} word /></h1>
    ${a.error?s`<p class="bad-text" data-tip=${a.error}>${a.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${be(a.steps)}</b> steps</span>
      <span><b>${Se(a.duration_s)}</b></span>
      <span data-tip=${a.created_at}>${U(a.created_at)}</span>
      <${Wn} path=${t} />
      <${W} icon="copy" label=${`Copy the run id ${a.id}`} onClick=${r} />
      <${Ft} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${As(a).map(([o,l])=>s`<tr><td class="muted">${o}</td><td>${l}</td></tr>`)}</table>
        <div class="menu-list">
          <button type="button" onClick=${()=>N(S(t,{run:a.id}),{replace:!0})}>
            <${v} name="panel-right" size=${15} /> Open in the side panel</button>
          <button type="button" onClick=${r}><${v} name="copy" size=${15} /> Copy the run id</button>
          ${a.git?.commit?s`<button type="button" onClick=${()=>navigator.clipboard?.writeText(a.git.commit)}>
            <${v} name="git-commit" size=${15} /> Copy the commit</button>`:null}
        </div>
      <//>
    </div>
    ${(n.proposals??[]).length?s`<div class="checks">
          ${n.proposals.map(o=>{let l=T("result",o.check);return s`<a class=${`check small tone-${l.tone}`} href=${S(o.group)} data-tip=${o.statement}>
              <${v} name=${l.icon} size=${14} />${o.group==="."?"own proposal":o.group}
              ${o.verdict?s`<${_} spec=${T("verdict",o.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function Wn({path:e}){let t=k($t(e)).data?.summary;if(!t)return null;let n=Object.entries(t.config??{}).map(([r,o])=>`${r} ${X(o)}`).join(", "),a=le(e.split("/").pop()??"");return s`<span data-tip=${`${t.stat} of ${t.metric} over ${a?"the run":"all runs"}`}>
    best <b>${t.metric} ${X(t.value)}</b>
    ${a?null:s` · <a href=${ce(t.run)}>${t.name}</a>${n?s` <em>(${n})</em>`:null}`}
  </span>`}function As(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,a])=>[n,String(a)])}var Gn=15e3;function Vn({node:e}){let t=ie(q),n=re(),[a,r]=Ht(),o=e.props.code,l=k(r&&o?{method:"code",params:o,scope:null}:null),[i,c]=g(null),[m,u]=g(120),[p,y]=g({error:null,warnings:[]}),b=w=>{de&&console.error(`[block ${e.id}] ${w}`),y(d=>({...d,error:w}))},C=O(()=>{});E(()=>{if(!i)return;let w=!0;Ne.n++;let d=()=>{w&&Ne.n--,w=!1};C.current=d;let $=setTimeout(()=>{w&&b(`no first render within ${Gn/1e3} s`),d()},Gn);return()=>{clearTimeout($),d()}},[i]),E(()=>{let w=i?.contentWindow;if(!w||l.status!=="ready")return;let d=M=>w.postMessage(M,"*"),$=new Map,h=new Zt,A=M=>{if(M.source!==w)return;let x=M.data;switch(x.type){case"hello":d({type:"init",init:{id:e.id,code:l.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:Bt.value,pair:Ae.value,prefs:dt(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics}});break;case"sub":if(!Xt.has(x.call.method)){d({type:"result",id:x.id,result:{status:"error",data:null,error:`${x.call.method} is not available in a custom block`,refreshing:!1}});break}$.get(x.id)?.(),$.set(x.id,Tt(x.call,se=>d({type:"result",id:x.id,result:se})));break;case"unsub":$.get(x.id)?.(),$.delete(x.id);break;case"navigate":x.url.startsWith("/")&&N(x.url);break;case"height":h.accept(performance.now())?u(Math.max(40,x.height)):B("its height keeps changing, so it is fixed at its last height");break;case"ready":y(se=>({...se,blank:x.blank,overflow:x.overflow})),C.current();break;case"warn":B(x.message);break;case"hover":rt.set(x.run);break;case"prefs":JSON.stringify(H.value)!==JSON.stringify(x.prefs)&&H.set(x.prefs);break;case"download":case"snapshot":x.href?Yt(x.href,x.name)?performance.now()-F>1e3&&(F=performance.now(),Pe().download(x.href,x.name)):B(`a download of ${x.name} was refused: only PNG, SVG and CSV files`):B("it draws no SVG or canvas to download");break;case"figure":Pe().figure(x.spec,x.name).catch(se=>B(`the PDF failed: ${se.message}`));break;case"expand":Jt(x.node)&&Pe().expand(x.node,t);break;case"error":b(x.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,P)),C.current();break;default:break}},B=M=>{de&&console.warn(`[block ${e.id}] ${M}`),y(x=>x.warnings.includes(M)?x:{...x,warnings:[...x.warnings,M]})},F=-1/0,H=dt(t.path),V=rt.subscribe(M=>d({type:"hover",run:M})),R=H.subscribe(M=>d({type:"prefs",prefs:M}));return addEventListener("message",A),d({type:"ping"}),()=>{V(),R(),removeEventListener("message",A);for(let M of $.values())M()}},[l.status,l.data?.code,i]),E(()=>{let w={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};i?.contentWindow?.postMessage(w,"*")},[t.names,t.colors,t.metrics,i]),E(()=>{n&&i?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let P=typeof o=="object"?o.path??o.block:String(o??"");At(e.id,{png:()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")});let f=r&&l.status==="ready"&&!p.error;return s`<div ref=${a} class="custom-block">
    <div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${f?s`<span class="chart-tools">
            <${W} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>i?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?s`<${W} icon="x" label="Close (Esc)" onClick=${()=>Le.set(null)} />`:s`<${W} icon="maximize" label="Expand" onClick=${()=>Pe().expand(e,t)} />`}
          </span>`:null}
    </div>
    <${ee} caption=${e.props.expanded?void 0:e.props.caption} result=${l}>
      ${p.error?s`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${P})</span>
            <pre class="code">${p.error}</pre>
          </div>`:null}
      ${p.warnings.map(w=>s`<${I} kind="warning">${w}<//>`)}
      ${f?s`<div class="custom-frame" data-frame-blank=${p.blank?"1":void 0} data-frame-overflow=${p.overflow?"1":void 0}>
            <iframe key=${l.data.code} ref=${c} sandbox="allow-scripts" ...${Ks()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${m}px`} />
          </div>`:null}
    <//>
  </div>`}function Ks(){if(!!1)return{src:Et("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1").replace(/@font-face\s*\{[^}]*\}/g,""),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}function qn({node:e}){let t=ae("main"),n=ie(q),a=t.data?.entries??[];return s`<${ee} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!a.length?s`<${I}>No images logged.<//>`:null}
    <div class="images">
      ${a.map(r=>s`<figure key=${`${r.run}/${r.path}`}>
          <img src=${Ct(_e(r.run,n.path),r.path)} alt=${r.caption??e.props.title} loading=${Re?"eager":"lazy"} />
          <figcaption class="small">step ${be(r.step)}${r.caption?` \xB7 ${r.caption}`:""}</figcaption>
        </figure>`)}
    </div>
  <//>`}function Xn({node:e}){let t=ae("main"),n=t.data?.entries??[];return s`<${ee} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?s`<${I}>No text logged.<//>`:null}
    ${n.map(a=>s`<div class="text-entry" key=${`${a.run}/${a.step}`}>
        <div class="muted small">step ${be(a.step)}${a.caption?` \xB7 ${a.caption}`:""}</div>
        <pre class="code">${a.text??""}</pre>
      </div>`)}
  <//>`}function Yn({node:e}){let[t,n]=g(Re||e.props.open!==!1),a=s`${(e.children??[]).map(l=>s`<${ne} key=${l.id} node=${l} />`)}`,r=ie(Fe);if(!e.props.title)return s`<div class="stack">${a}</div>`;let o=r===e.props.title.toLowerCase();return s`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${t} aria-label=${o?`${t?"Close":"Open"} ${e.props.title}`:void 0}
        data-tip=${o?`${t?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${()=>n(!t)}>
      <${v} name=${t?"chevron-down":"chevron-right"} size=${16} />${o?null:e.props.title}
    </button>
    ${t?s`<div class="stack">${a}</div>`:null}
  </div>`}function Jn({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return s`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>s`<${ne} key=${n.id} node=${n} />`)}
  </div>`}function Zn({node:e}){let t=ie(q),n=We(t.path),a=e.props.min_width??320,r=e.props.columns,o=r?`grid-template-columns: repeat(${r}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${a}px, 100%), 1fr))`,l=(e.children??[]).flatMap(u=>u.props.y??[]),i=e.props.addable?n.added.filter(u=>!l.includes(u)).map(u=>({block:"line",id:`added-${u}`,props:{y:u,added:!0},data:{main:{...e.props.template,params:{...e.props.template.params,y:[u]}}}})):[],c=qt([...e.children??[],...i],n.order[e.id]),m=(u,p)=>{let y=c.map(b=>b.id).filter(b=>b!==u);y.splice(y.indexOf(p),0,u),Gt(t.path,e.id,y)};return s`<div class="grid" style=${o}>
    ${c.map(u=>s`<${Us} key=${u.id} node=${u} path=${t.path} span=${n.spans[u.id]??u.props.span??1}
      columns=${r} onDrop=${p=>p!==u.id&&m(p,u.id)} />`)}
    ${e.props.addable&&!!1?s`<${Fs} path=${t.path} shown=${[...l,...n.added]} />`:null}
  </div>`}var bt=[1,2,"full"];function Us(e){let[t,n]=g(!1),a=bt[(bt.indexOf(e.span)+1)%bt.length],r=o=>o==="full"?"full width":`${o} column${o===1?"":"s"}`;return s`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${o=>{o.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${o=>{o.preventDefault(),n(!1),e.onDrop(o.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${o=>o.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${v} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${r(e.span)}; click for ${r(a)}`}
        aria-label=${`Width ${r(e.span)}`} onClick=${()=>Vt(e.path,e.node.id,a)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${ne} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function Fs(e){let t=k({method:"keys",params:{from:e.path},scope:e.path}).data,n=(t?.metrics?.rows??[]).map(a=>a[0]).filter(a=>!e.shown.includes(a));return t&&!n.length?null:s`<div class="add-chart">
    <span class="add-chart-label"><${v} name="plus" size=${16} /> Add a chart</span>
    <${je} single options=${n} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
      onChange=${([a])=>Ge(e.path,r=>({added:[...r.added,a]}))} />
  </div>`}function Qn({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[a,r]=g(()=>t.find(i=>i.id===n())?.id??t[0]?.id),o=i=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(i)}`),r(i)},l=t.find(i=>i.id===a)??t[0];return Re?s`<div class="stack">${t.map(i=>s`<${ne} key=${i.id} node=${i} />`)}</div>`:s`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(i=>s`<button type="button" role="tab" id=${`tab-${i.id}`} aria-selected=${i.id===l?.id}
          aria-controls=${`panel-${i.id}`} onClick=${()=>o(i.id)}>${i.props.title??i.id}</button>`)}
    </div>
    ${l?s`<div class="stack" role="tabpanel" id=${`panel-${l.id}`} aria-labelledby=${`tab-${l.id}`}>
          ${(l.children??[]).map(i=>s`<${ne} key=${i.id} node=${i} />`)}
        </div>`:null}
  </div>`}var js={section:Yn,row:Jn,grid:Zn,line:rn,table:un,stat:dn,images:qn,text:Xn,proposal:On,note:Un,output:An,memory:In,groups:zn,notes:Bn,tabs:Qn,scatter:on,bar:ln,histogram:cn,data_table:tn,timeline:nn,custom:Vn,markdown:Kn};function ne({node:e}){return s`<${jt} node=${e} blocks=${js} />`}function es(e,t){let n=e.split(`
`),a=t.split(`
`),r=n.length,o=a.length,l=Array.from({length:r+1},()=>new Uint32Array(o+1));for(let u=r-1;u>=0;u--)for(let p=o-1;p>=0;p--)l[u][p]=n[u]===a[p]?l[u+1][p+1]+1:Math.max(l[u+1][p],l[u][p+1]);let i=[],c=0,m=0;for(;c<r&&m<o;)n[c]===a[m]?(i.push({kind:"same",text:n[c]}),c++,m++):l[c+1][m]>=l[c][m+1]?i.push({kind:"removed",text:n[c++]}):i.push({kind:"added",text:a[m++]});for(;c<r;)i.push({kind:"removed",text:n[c++]});for(;m<o;)i.push({kind:"added",text:a[m++]});return i}function ts(e,t=3){let n=[],a=0;for(;a<e.length;){if(e[a].kind!=="same"){n.push(e[a++]);continue}let r=a;for(;r<e.length&&e[r].kind==="same";)r++;let o=a===0?0:t,l=r===e.length?0:t;r-a>o+l+1?n.push(...e.slice(a,a+o),{kind:"skip",count:r-a-o-l},...e.slice(r-l,r)):n.push(...e.slice(a,r)),a=r}return n}var yt={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",timeline:"timeline",proposal:"predictions"};function ns(e){if(yt[e.block])return yt[e.block];if(e.block==="row"||e.block==="grid"){if(e.props.addable)return"charts";let n=new Set((e.children??[]).map(r=>yt[r.block])),[a]=n;if(n.size===1&&a)return a}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function nt(e){let t=k(Ie(e.path)),n=re(),a=L(t.data),r=De(()=>Ue(a.map(u=>u["run.id"]),n),[t.data,n]),o=De(()=>new Map(a.map(u=>[u["run.id"],u["run.name"]??u["run.id"]])),[t.data]),l=e.plain?"view plain":"sections view";if(!e.view)return s`<div class=${l}>${e.before}
      ${e.plain?s`<div class="skeleton late" style="block-size: 320px"></div>`:s`<${z} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let i={path:e.path,colors:r,names:o,metrics:e.view.metrics??{}},c=e.view.view;if(e.plain)return s`<div class=${l}><${q.Provider} value=${i}><${ne} node=${c} /><//></div>`;let m=c.block==="section"&&!c.props.title?c.children??[]:[c];return s`<div class=${l}>${e.before}
    <${q.Provider} value=${i}>
      ${m.map(u=>{let p=ns(u);return s`<${z} key=${u.id} label=${p}><${Fe.Provider} value=${p}><${ne} node=${u} /><//><//>`})}
    <//>
  </div>`}function ss(e){if(null)return s`<div class="view-source small"><${v} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=D(G),a=n.page==="group"&&n.version,r=t.versions?s`<a href=${S(e.path,{history:!0})}><${v} name="history" size=${14} /> history (${t.versions})</a>`:null,o;switch(t.source){case"draft":o=s`draft <b>${t.draft}</b>`;break;case"view":o=s`${t.title?s`<em>${t.title}</em> · `:null}saved ${U(fe(t.version))} by ${t.author??"unknown"}`;break;default:o=s`the built-in view`}return s`<div class="view-source small">
    <${v} name="layout" size=${14} /><span>${o}</span>
    ${a?s`<a href=${S(e.path)}>an older version · show the current one</a>`:null}
    ${r}
    ${t.outdated?.length&&!a?s`<${Ws} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||a?null:s`<${Gs} path=${e.path} />
        <${Vs} path=${e.path} view=${t} />`}
  </div>`}function Ws(e){let[t,n]=g(null),a=e.outdated.map(o=>o.name).join(", ");return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{await vn(e.path)}catch(o){n(o.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${a} exists; update re-pins this view to it (a new version)`}>
      <${v} name="update" size=${14} /> update ${a}</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function Gs(e){let[t,n]=g(null);return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{Ce.set(await Ve(e.path,null,""))}catch(r){n(r.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${v} name="file-text" size=${14} /> add text</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function Vs(e){let t=We(e.path),n=Wt(t),[a,r]=g(!1),[o,l]=g(e.view.title??""),[i,c]=g(e.view.finding??""),[m,u]=g(null),[p,y]=g(!1);if(!n&&!a)return null;let b=async C=>{C.preventDefault(),y(!0),u(null);try{let P={charts:t.charts,added:t.added,order:t.order,spans:t.spans};await K("save_view",{path:e.path,prefs:P,title:o,finding:i}),Ge(e.path,()=>({view:{},charts:{},added:[],order:{},spans:{}})),xe(f=>["view","view_history","summary"].includes(f.method)&&f.scope===e.path),r(!1)}catch(P){u(P.message)}finally{y(!1)}};return a?s`<form class="save-form" onSubmit=${b}>
    <${Oe} label="Title"><input value=${o} onInput=${C=>l(C.target.value)} /><//>
    <${Oe} label="Finding"><input value=${i} placeholder="the key result in one sentence"
        onInput=${C=>c(C.target.value)} /><//>
    <div class="save-actions">
      <${te} type="submit" icon=${p?"hourglass":"save"} disabled=${p}>${p?"Saving\u2026":"Save as view"}<//>
      <${te} icon="x" kind="quiet" onClick=${()=>r(!1)}>Cancel<//>
      ${m?s`<span class="bad-text small">${m}</span>`:null}
    </div>
  </form>`:s`<${te} icon="save" class="save-view" onClick=${()=>r(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function as(e){let t=k(Nn(e.path)),n=t.data?.entries??[],[a,r]=g(null),o=a??n.slice(0,2).map(i=>i.version).reverse(),l=i=>{let c=o.includes(i)?o.filter(m=>m!==i):[...o,i].slice(-2);r(c.sort())};return t.status==="error"?s`<${I} kind="error">${t.error}<//>`:s`<section class="history">
    <h2 class="history-title heading"><${v} name="history" size=${16} /> View history</h2>
    ${t.data&&!n.length?s`<${I}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((i,c)=>s`<li key=${i.version} class=${o.includes(i.version)?"picked":""}>
          <label><input type="checkbox" checked=${o.includes(i.version)} onChange=${()=>l(i.version)} />
            <span class="num muted" data-tip=${i.version}>${U(i.time)}</span>
            <b>${i.title??"untitled"}</b><span class="muted">${i.author??""}</span>
            ${i.message?s`<span>${i.message}</span>`:null}</label>
          <a href=${c===0?S(e.path):S(e.path,{version:i.version})}
            onClick=${m=>{m.preventDefault(),N(c===0?S(e.path):S(e.path,{version:i.version}))}}>${c===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${o.length===2?s`<${qs} path=${e.path} a=${o[0]} b=${o[1]} />`:null}
  </section>`}function qs(e){let t=i=>({method:"view_show",params:{group:e.path,version:i},scope:e.path}),n=k(t(e.a)).data,a=k(t(e.b)).data,r=k(pe(e.path,e.a)).data,o=k(pe(e.path,e.b)).data,l=n&&a?ts(es(n.yaml,a.yaml)):[];return s`<div class="compare">
    <h3 class="block-title heading">Changes from ${U(fe(e.a))} to ${U(fe(e.b))}</h3>
    <pre class="diff code">${l.map(i=>i.kind==="skip"?s`<div class="diff-skip">⋯ ${i.count} unchanged lines</div>`:s`<div class=${`diff-${i.kind}`}>${i.kind==="added"?"+ ":i.kind==="removed"?"\u2212 ":"  "}${i.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${r?.title??e.a}</h3><${nt} path=${e.path} view=${r} plain /></div>
      <div><h3 class="block-title heading">${o?.title??e.b}</h3><${nt} path=${e.path} view=${o} plain /></div>
    </div>
  </div>`}function rs(e){return E(()=>{document.title=`${e.path==="."?"local":e.path} \xB7 Beamtime`},[e.path]),e.history?s`<div class="page"><div class="sections">
      <${z} label=${os(e.path)}><${vt} path=${e.path} /><//>
      <${z} label="history"><${as} path=${e.path} /><//>
    </div></div>`:s`<div class="page">
    <${Xs} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function Xs(e){let t=k(pe(e.path,e.version,e.draft));E(()=>{t.status==="ready"&&requestAnimationFrame(Rt)},[t.status==="ready"]);let n=s`
    <${z} label=${os(e.path)}>
      <${vt} path=${e.path} finding=${t.data?.finding} />
      ${t.data?s`<${ss} path=${e.path} view=${t.data} />`:null}
    <//>
    ${le(e.path.split("/").pop()??"")?null:s`<${jn} path=${e.path} />`}`;return t.status==="error"?s`<div class="sections">${n}
      <${z} label="view">
        ${Ys(e.path,t.error)?s`<${I} kind="warning">${t.error} The page fills in once the remote answers again.<//>`:s`<${I} kind="error">${t.error}<//>`}
      <//>
    </div>`:s`<${nt} path=${e.path} view=${t.data} before=${n} />`}function os(e){return le(e.split("/").pop()??"")?"run":"group"}function Ys(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function is(e){E(()=>{ke(pe(e.id)).then(n=>N(S(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=k(pe(e.id));return t.status==="error"?s`<div class="page"><${I} kind="error">${t.error}<//></div>`:s`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var Js={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},wt=20,Me=-1,Zs=[["day",86400],["week",7*86400],["month",30*86400]];function cs(e){let t=L(k(oe()).data).map(i=>i.path),n=k({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),a=k({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});E(()=>{document.title="Timeline \xB7 Beamtime"},[]);let r=Date.now()/1e3,o=L(n.data).filter(i=>i["run.created_at"]).map((i,c)=>({id:i["run.id"],name:i["run.name"]??i["run.id"],group:i["run.group"],status:i["run.status"],start:Date.parse(i["run.created_at"])/1e3,end:i["run.ended_at"]?Date.parse(i["run.ended_at"])/1e3:r,lane:c})),l=(a.data?.entries??[]).map(i=>({id:i.id,type:i.type,group:i.group,description:i.description,t:Date.parse(fe(i.id))/1e3}));return s`<div class="page timeline-page"><div class="sections">
    <${z} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${Oe} label="Group" inline>
          <select value=${e.from} onChange=${i=>N(He(i.target.value),{replace:!0})}>
            ${t.map(i=>s`<option value=${i}>${i==="."?"everything":i}</option>`)}
          </select><//>
        <span class="muted small">${o.length} runs · ${l.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${z} label="runs">
      ${n.status==="error"?s`<${I} kind="error">${n.error}<//>`:null}
      ${n.data&&a.data?s`<${Qs} bars=${o} marks=${l} />`:s`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function Qs(e){let t=re(),n=O(null),a=[...e.bars.flatMap(f=>[f.start,f.end]),...e.marks.map(f=>f.t)],r=a.length?ls(Math.min(...a),Math.max(...a)):ls(Date.now()/1e3-86400,Date.now()/1e3),[o,l]=g(r),i=e.bars.length,c=Math.min(900,Math.max(160,(i+1.5)*wt+40)),u=sn(n,an,t?(f=>{let w=Qt(o[0],o[1]),d=h=>f.colors[Js[h]??"muted"],$=h=>f.colors[h==="verdict"?"good":h==="decision"?"accent":h==="question"?"warn":"muted"];return{style:zt(f),height:c,x:{range:o,log:!1,format:h=>en(h,w.step),splits:w.at},y:{range:[Me-.8,i+.5],log:!1,reverse:!0,size:150,splits:i<=40?[Me,...e.bars.map(h=>h.lane)]:[Me],format:h=>h===Me?"notes":aa(e.bars[Math.round(h)]?.name??"")},draw:({ctx:h,x:A,y:B,px:F,focused:H})=>{let V=wt*.62*F;for(let R of e.bars){let M=A(R.start),x=Math.max(3*F,A(R.end)-M);h.fillStyle=H!==null&&H!==R.id?It(d(R.status),.35):d(R.status),h.beginPath(),h.roundRect(M,B(R.lane)-V/2,x,V,3*F),h.fill()}for(let R of e.marks){let M=A(R.t),x=B(Me),se=(H===R.id?6:4.5)*F;h.fillStyle=$(R.type),h.beginPath(),h.moveTo(M,x-se),h.lineTo(M+se,x),h.lineTo(M,x+se),h.lineTo(M-se,x),h.closePath(),h.fill()}},hit:(h,A,B,F)=>{if(Math.abs(A-F(Me))<wt/2){let R=sa(e.marks,M=>Math.abs(B(M.t)-h),8);return R?{key:R.id,rows:ta(R)}:null}let H=Math.round((A-F(0))/(F(1)-F(0))),V=e.bars.find(R=>R.lane===H&&B(R.start)-3<=h&&h<=Math.max(B(R.end),B(R.start)+3)+3);return V?{key:V.id,rows:ea(V)}:null},onClick:h=>{let A=e.marks.find(B=>B.id===h);A?N(S(A.group,{drawer:!0})):N(ce(h))}}})(t):null,[o,e.bars,e.marks],t),p=f=>{if(!u.current)return;f.preventDefault();let w=u.current.xAt(f.clientX),d=Math.exp(f.deltaY*.0015);l(([$,h])=>kt([w-(w-$)*d,w+(h-w)*d],r))},y=O(null),b=f=>y.current={x:f.clientX,range:o},C=f=>{if(!y.current||!u.current||!(f.buttons&1))return;let w=(f.clientX-y.current.x)*u.current.xPerPixel(),[d,$]=y.current.range;Math.abs(f.clientX-y.current.x)>3&&l(kt([d-w,$-w],r))},P=Math.max(...a,Date.now()/1e3);return s`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${Zs.map(([f,w])=>s`<button type="button" role="radio" aria-checked=${Math.abs(o[1]-o[0]-w)<1}
          onClick=${()=>l(kt([P-w,P+w*.02],[Math.min(r[0],P-w),r[1]]))}>last ${f}</button>`)}
      <button type="button" role="radio" aria-checked=${o[0]===r[0]&&o[1]===r[1]} onClick=${()=>l(r)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${c}px`}
      onWheel=${p} onPointerDown=${b} onPointerMove=${C} onPointerUp=${()=>y.current=null}></div>
    <p class="muted small">${na(t)}</p>
  </div>`}function ea(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:U(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:Se(e.end-e.start),color:null}]}function ta(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:U(new Date(e.t*1e3).toISOString()),color:null}]}function na(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function sa(e,t,n){let a=null,r=n;for(let o of e){let l=t(o);l<r&&([a,r]=[o,l])}return a}function ls(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function kt([e,t],n){let a=Math.min(n[1]-n[0],Math.max(60,t-e)),r=Math.max(n[0],Math.min(e,n[1]-a));return[r,r+a]}function aa(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function ds(){let e=D(Le),t=O(null);if(E(()=>{let r=t.current;if(!r||!e)return;r.showModal();let o=()=>Le.set(null);return r.addEventListener("close",o),()=>r.removeEventListener("close",o)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},a=String(n.props.title??n.props.y??"Chart");return s`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${a} closedby="any">
    <${q.Provider} value=${e.view}><${ne} node=${n} /><//>
  </dialog>`}function us(e,t){let n=e.toLowerCase(),a=t.toLowerCase();if(!n)return 1;let r=a.indexOf(n);if(r>=0)return 100-Math.min(r,50)-a.length/100;let o=0,l=0;for(let i of a)if(i===n[o]?o++:o>0&&l++,o===n.length)return 40-Math.min(l,39);return 0}function ps(e){let[t,n]=g(e.query),[a,r]=g(0),o=O(null),l=L(k(oe()).data),i=L(k(Qe()).data);E(()=>{let d=o.current;d.showModal();let $=()=>J.set(null);d.addEventListener("close",$);let h=!1,A=H=>{let V=d.getBoundingClientRect();return H.clientX<V.left||H.clientX>V.right||H.clientY<V.top||H.clientY>V.bottom},B=H=>h=A(H),F=H=>h&&A(H)&&d.close();return"closedBy"in HTMLDialogElement.prototype||(d.addEventListener("pointerdown",B),d.addEventListener("pointerup",F)),()=>{d.removeEventListener("close",$),d.removeEventListener("pointerdown",B),d.removeEventListener("pointerup",F)}},[]);let c=()=>o.current?.close(),m=d=>()=>N(d),u=G.value,p=u.page==="group"?u.path:".",y=(d,$,h,A)=>({section:"Commands",label:d,detail:$,sym:{icon:h,tone:"muted",label:d},run:A}),C=[...l.map(d=>({section:"Groups",label:d.path==="."?"local":d.path,detail:`${d.runs} runs${d.proposal?` \xB7 ${d.proposal}`:""}`,sym:T("research",d.status),run:m(S(d.path))})),...i.map(d=>({section:"Runs",label:d["run.name"]??d["run.id"],detail:`${d["run.status"]} \xB7 ${d["run.path"]}`,sym:T("run",d["run.status"]),run:m(S(d["run.path"]))})),y("Theme: light","","sun",()=>Ke("light")),y("Theme: dark","","moon",()=>Ke("dark")),y("Theme: follow the system","","monitor",()=>Ke("system")),y("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),y("Show notes and timeline","i","file-text",m(S(p,{drawer:!0}))),y("Show or hide the sidebar","\u2318B","panel-left",()=>Y.set(!Y.value)),y(Q.value?"Resume live updates":"Pause live updates","p",Q.value?"play":"pause",()=>Q.set(!Q.value)),y("Keyboard shortcuts","?","keyboard",()=>me.set(!0)),y("Settings","","settings",m("/settings/appearance"))].map(d=>({it:d,s:Math.max(us(t,d.label),us(t,d.detail)*.5)})).filter(d=>d.s>0).sort((d,$)=>$.s-d.s||ms(d.it.section)-ms($.it.section)).slice(0,60).map(d=>d.it),P=d=>{d&&(c(),d.run())},f=d=>{if(d.key==="ArrowDown")r(Math.min(C.length-1,a+1));else if(d.key==="ArrowUp")r(Math.max(0,a-1));else if(d.key==="Enter")P(C[a]);else return;d.preventDefault()},w="";return s`<dialog class="sheet" ref=${o} aria-label="Search" closedby="any">
    <div class="palette-input"><${v} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${C[a]?`pal-${a}`:void 0}
        onInput=${d=>{n(d.target.value),r(0)}} onKeyDown=${f} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${C.map((d,$)=>{let h=d.section!==w&&!t?w=d.section:null;return s`${h?s`<li class="palette-head small" role="presentation">${h}</li>`:null}
          <li id=${`pal-${$}`} class="item" role="option" aria-selected=${$===a}
              onMouseMove=${()=>r($)} onClick=${()=>P(d)}>
            <${_} spec=${d.sym} /><span class="label">${d.label}</span><span class="detail small">${d.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function ms(e){return["Groups","Runs","Commands"].indexOf(e)}function st(e,t=[]){let n=new Map,a=(o,l={})=>({path:o,name:o==="."?"local":o.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let o of e)n.set(o.path,a(o.path,o));n.has(".")||n.set(".",a("."));for(let o of t)o.name!=="local"&&(n.has(o.name)||n.set(o.name,a(o.name)),Object.assign(n.get(o.name),{state:o.state,error:o.error}));for(let o of n.values()){if(j(o.path))continue;let l=o.path.lastIndexOf("/"),i=l<0?".":o.path.slice(0,l);(n.get(i)??n.get(ve(o.path))??n.get(".")).children.push(o)}for(let o of n.values())o.children.sort((l,i)=>l.name.localeCompare(i.name));let r=[...n.values()].filter(o=>o.path!=="."&&j(o.path)).sort((o,l)=>o.name.localeCompare(l.name));return[n.get("."),...r]}function $s(e,t,n,a=new Set){let r=[],o=n.toLowerCase(),l=i=>{(!o||i.path.toLowerCase().includes(o)||fs(i,o))&&(r.push(i),(o||(j(i.path)?!a.has(i.path):t.has(i.path)))&&i.children.forEach(l))};return e.forEach(l),r}function fs(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||fs(n,t))}function hs(e,t){if(j(t))return e;let n=t.lastIndexOf("/"),a=n<0?".":t.slice(0,n),r=o=>o.path===a?o:o.children.map(r).find(l=>l)??null;return e.map(r).find(o=>o)?.children??[]}function gs(e){return j(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function vs(){let e=D(G),t=k(oe()),[n,a]=g(()=>new Set(ye("open",[]))),[r,o]=g(()=>new Set(ye("closed-hosts",[]))),[l,i]=g(""),c=O(null),m=e.page==="group"?e.path:null,u=st(L(t.data),t.data?.meta?.sources??[]),p=$s(u,ia(n,m),l,r),y=f=>j(f)?!r.has(f):n.has(f),b=(f,w)=>{let d=w??!y(f);if(j(f)){let h=new Set(r);d?h.delete(f):h.add(f),we("closed-hosts",[...h]),o(h);return}let $=new Set(n);d?$.add(f):$.delete(f),we("open",[...$]),a($)},C=O(m);return E(()=>{m!==C.current&&m&&!j(m)&&r.has(ve(m))&&b(ve(m),!0),C.current=m},[m]),s`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${v} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${l} aria-label="Filter groups"
        onInput=${f=>i(f.target.value)} />
    </label>
    <div class="tree" ref=${c} onKeyDown=${f=>{let w=[...c.current?.querySelectorAll("a.tree-item")??[]],d=w.indexOf(document.activeElement),$=p[d];switch(f.key){case"ArrowDown":w[Math.min(w.length-1,d+1)]?.focus();break;case"ArrowUp":w[Math.max(0,d-1)]?.focus();break;case"ArrowRight":$?.children.length&&b($.path,!0);break;case"ArrowLeft":$?.children.length&&y($.path)?b($.path,!1):$&&w[p.findIndex(h=>h.path===oa($.path))]?.focus();break;default:return}f.preventDefault()}} role="tree">
      ${p.map(f=>s`<${ra} key=${f.path} node=${f} current=${f.path===m}
        open=${y(f.path)||!!l} onToggle=${()=>b(f.path)} />`)}
    </div>
  </nav>`}function ra(e){let t=e.node,n=()=>ze(t.path),a=t.children.length>0,r=t.state==="unreachable";return s`<a class=${`tree-item${e.current?" current":""}${t.path.startsWith("@")&&j(t.path)?" source-root":""}`} href=${S(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${a?e.open:void 0}
      style=${`padding-inline-start:${8+gs(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${o=>{o.metaKey||o.ctrlKey||(o.preventDefault(),N(S(t.path)))}}>
    <span class="twisty" onClick=${o=>{o.preventDefault(),o.stopPropagation(),e.onToggle()}}>
      ${a?s`<${v} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    ${j(t.path)?s`<${_} size=${14} spec=${{icon:r?"cloud-off":"server",tone:"muted",label:r?`Unreachable: ${t.error??"no answer"}`:t.path==="."?"This machine":`Remote host ${t.name}`}} />`:null}
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?s`<${_} spec=${T("run","running")} size=${14} />`:null}
      ${t.failed?s`<${_} spec=${{...T("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function oa(e){if(j(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function ia(e,t){if(!t||t===".")return e;let n=new Set(e),a=t.split("/");for(let r=1;r<a.length;r++)n.add(a.slice(0,r).join("/"));return n}function ys(){let e=D(G),t=D(Y),n=D(J),a=D(me),r=O(null);E(()=>_t(()=>r.current),[]),E(()=>(addEventListener("keydown",bs),()=>removeEventListener("keydown",bs)),[]);let o=e.page==="group"&&e.drawer,l;switch(e.page){case"group":l=s`<${rs} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":l=s`<${is} id=${e.id} />`;break;case"settings":l=s`<${xn} />`;break;case"timeline":l=s`<${cs} key=${e.from} from=${e.from} />`;break;default:l=s`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return de||!1?s`<main class="main render-main" ref=${r}>${l}</main>`:s`<div class=${`shell${t?"":" no-sidebar"}${o?" with-drawer":""}`}>
    <${Rn} />
    ${t?s`<${vs} />`:null}
    <main class="main" ref=${r}>${l}</main>
    ${o?s`<${Fn} path=${e.path} run=${e.run} />`:null}
    <${Ln} />
    ${n!==null?s`<${ps} query=${n} />`:null}
    ${a?s`<${ca} />`:null}
    <${ds} />
  </div>`}function bs(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),J.set(J.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),Y.set(!Y.value);return}if(e.key==="Escape"){if(J.value!==null||me.value)return;let a=G.value;return a.page==="group"&&a.run?N(S(a.path,{drawer:!0}),{replace:!0}):a.page==="group"&&a.drawer?N(S(a.path),{replace:!0}):void 0}if(t||e.altKey||wn(e)||J.value!==null||me.value)return;let n=G.value;switch(e.key){case"/":e.preventDefault(),J.set("");break;case"?":me.set(!me.value);break;case"p":Q.set(!Q.value);break;case"i":n.page==="group"&&N(S(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":Y.set(!Y.value);break;case"[":case"]":n.page==="group"&&la(n.path,e.key==="]"?1:-1);break}}async function la(e,t){let n=await ke(oe()),a=hs(st(L(n),n?.meta?.sources??[]),e),r=a.findIndex(l=>l.path===e),o=a[r+t];o&&N(S(o.path))}function ca(){let e=O(null);return E(()=>{let t=e.current;t.showModal();let n=()=>me.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),s`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${qe.map(([t,n])=>s`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${te} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}Lt();if(de){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(ue.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Ne.n,Pt&&Kt()}mn();var da=K("meta").then(e=>(de&&(e={...e,settings:{...e.settings,theme_mode:ue.value}}),Xe(e),e));!de&&!!1&&Nt(async()=>{let[e,t]=await Promise.all([da,K("meta")]);e.bundle!==t.bundle?location.reload():Xe(t)});xt(s`<${ys} />`,document.getElementById("app"));
