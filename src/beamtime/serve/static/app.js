import{$ as ot,$a as jn,A as dn,Aa as Cn,B as Le,Ba as qe,C as ie,Ca as ct,D as E,Da as Tt,E as nt,F as oe,Fa as Sn,G as pe,H as De,Ha as Mt,I as X,Ia as En,J as U,K as pn,La as Tn,M as P,Ma as Mn,N as mn,Na as Dn,O as $n,Oa as In,P as le,Pa as _n,Q as Ue,Qa as On,R as fn,Ra as zn,S as st,T as Ne,Ta as Bn,U as ge,V as vn,Va as An,W as St,Wa as Hn,X as rt,Xa as Kn,Y as F,Ya as Un,Z as Y,Za as Fn,_ as me,_a as Wn,a as r,aa as yn,b as en,c as Ae,ca as Ie,d as re,da as be,e as tt,fa as wn,ga as kn,h as tn,ha as x,i as nn,ia as z,j as He,ja as at,k as sn,ka as Q,l as rn,la as R,m as on,ma as L,na as We,oa as _,pa as Se,q as j,qa as B,r as Ke,ra as ee,s as Re,sa as je,t as Ct,ta as Ve,u as w,ua as it,v as an,va as lt,w as ae,wa as I,x as ln,xa as Ge,y as cn,ya as Et,z as un,za as xn}from"./chunks/chunk-OOMQQ2UH.js";import{a as Qt,b as Qe}from"./chunks/chunk-O2K4N3UR.js";import{$ as Rn,C as fe,D,E as Ce,F as he,K as hn,M as Fe,Q as gn,R as bn,V as Nn,_ as Pn,aa as Ln,b as Yt,ba as Dt,d as Zt,f as y,g as T,h as Jt,i as N,j as Te,k as J,q as G,r as xt,t as ke,u as de,v as Me,w as et,x as W,y as xe}from"./chunks/chunk-INFK5EOL.js";import"./chunks/chunk-VC46IEJQ.js";function Vn({size:e=16}){return r`<svg class="mark" width=${e} height=${e} viewBox="0 0 24 24" aria-hidden="true">
    <path d="M2.5 19.5 L9.5 4.5" /><path class="mark-2" d="M8.5 19.5 L15.5 4.5" /><path class="mark-3" d="M14.5 19.5 L21.5 4.5" />
  </svg>`}function Pe(e,t){Le(n=>t.includes(n.method)&&n.scope!==null&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var Nt=["notes","timeline","groups","check","card","memory_show","status"];async function ut(e,t){let n=e.meta??{};await j("note_add",{group:e.group,type:t.type??e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),Pe(e.group,Nt)}async function Gn(e,t,n,s){await j("note_add",{group:e,type:t,description:n,body:s}),Pe(e,Nt)}async function qn(e,t){await j("memory_update",{group:e,body:t}),Pe(e,["memory_show","status"])}async function Xn(e,t){let n=await j("proposal_show",{group:e}),s=Object.fromEntries(Object.entries(n.proposal??{}).filter(([o])=>!["schema","author","user","supersedes"].includes(o)));await j("proposal_set",{group:e,proposal:{...s,statement:t}}),Pe(e,["groups","proposal_show","check","summary"])}async function Yn(e){await j("note_rm",{note:e.id}),Pe(e.group,Nt)}async function Zn(e,t,n){await j("name",{run:e,name:n}),Pe(t,["card","runs","groups","summary","series"])}async function Pt(e,t){await j("run_promote",{runs:[pe(e,t)]}),Pe(t,["card","runs","groups","summary","series","keys","check","proposal_show","status"])}async function dt(e,t,n){let s=await j("view_text",{path:e,id:t,text:n});return Le(o=>["view","view_history"].includes(o.method)&&o.scope===e),s.id}async function Jn(e){await j("view_upgrade",{group:e}),Le(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var _e=new fe(null);async function Qn(e,t){return await j("set",{key:e,value:t}),j("meta")}var $e=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),ve=(e,t=null,n=null,s=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{},...s?{metrics:s}:{}},scope:e}),Rt=(e,t=null)=>({method:"summary",params:{path:e,...t?{metrics:t}:{}},scope:e}),Oe=e=>({method:"groups",params:{from:e,depth:0},scope:e}),es=e=>({method:"check",params:{group:e},scope:e}),ts=e=>({method:"proposal_show",params:{group:e},scope:e}),ze=(e,t)=>({method:"card",params:{run:pe(e,t)},scope:t}),ns=(e,t)=>({method:"output",params:{run:pe(e,t),tail:30},scope:t}),ss=(e,t)=>({method:"run_diff",params:{run:pe(e,t)},scope:t}),Xe=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),rs=e=>({method:"runs",params:{from:e,hidden:!0,where:{"run.hidden":!0},select:["run.name","run.status","run.created_at"],limit:200},scope:e}),pt=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),os=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),as=()=>({method:"status",params:{},scope:"."}),mt=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function Ye(e){let t=Ae(e).value.main;for(let n of[ve(e,null,null,t),Oe(e),Xe(e),Rt(e,t)])Ct(n);Re(ve(e,null,null,t)).then(n=>{for(let s of is(n.view))Ct(s)}).catch(()=>{})}function is(e){return e?[...Sr.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(is)]:[]}var Sr=new Set(["line","custom"]),ls=e=>({method:"view_history",params:{group:e},scope:e});var Er="/static/favicon.svg",Tr="/static/favicon-live.svg";function Mr(e){if(!1)return;let t=document.querySelector("link[rel=icon]");if(!(t instanceof HTMLLinkElement))return;let n=e?Tr:Er;t.getAttribute("href")!==n&&(t.type="image/svg+xml",t.href=n)}function Ze(e,t=0){T(()=>{document.title=`${t?`(${t}) `:""}${e} \xB7 Beamtime`,Mr(t>0)},[e,t])}function cs(e){let t=ie(e.split("/").pop()??""),n=w(t?null:Oe(e)),s=w(t?ze(e.split("/").pop()??"",e):null),o=t?s.data?.run.name??s.data?.run.id??e:e==="."?"local":e.split("/").pop()??e,i=t?s.data?.run.status==="running"?1:0:L(n.data)[0]?.running??0;Ze(o,i)}var te=new fe(Ce("sidebar",!0)),ne=new fe(null),ye=new fe(!1),we=new fe(null);te.subscribe(e=>he("sidebar",e));var us=Ce("visit",Date.now());he("visit",Date.now());function ds(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var $t=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var Dr=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function ft(e){we.set(e),un(e.stale),st.set(e.theme),Fe.set(e.colormaps),e.settings?.theme_mode&&ge.set(e.settings.theme_mode),St()}var ps=0;async function Lt(e,t){let n=++ps;e==="theme_mode"&&(ge.set(t),St());let s=await Qn(e,t);n===ps&&ft(s)}function ms(){let e=D(ge),t=me(),n=D(we),[s,o]=y(null);Ze("Settings");let i=(c,u)=>{o(null),Lt(c,u).catch($=>o($.message))},l=n?.settings??{},a=(c,u,$)=>r`
    <label class="field-label small" for=${`setting-${c}`}>${u}</label>
    <span class="input body">
      <select id=${`setting-${c}`} value=${l[c]} onChange=${d=>i(c,d.target.value)}>
        ${$.map(d=>r`<option value=${d}>${d}</option>`)}
      </select>
    </span>`;return r`<div class="page settings"><div class="sections">
    <${B} label="settings">
      <h1 class="page-title title" tabindex="-1">Settings</h1>
      <p class="muted small">Changes are written to <code>${l.file??"beamtime.yaml"}</code>, the project's settings.</p>
      ${s?r`<${R} kind="error">${s}<//>`:null}
    <//>
    <${B} label="appearance">
      <div class="settings-rows">
        <span class="field-label small">Mode</span>
        <div class="segmented" role="radiogroup" aria-label="Theme mode">
          ${Dr.map(([c,u,$])=>r`<button type="button" role="radio" aria-checked=${e===c} onClick=${()=>i("theme_mode",c)}>
            <${x} name=${u} size=${15} />${$}</button>`)}
        </div>
        ${a("theme","Theme",n?.themes??[])}
      </div>
      <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files recolor this layout: they go in <code>themes/</code> next to
        beamtime.yaml. Colormaps are chosen in each chart's settings.</p>
      ${(n?.theme?.problems??[]).map(c=>r`<${R} kind="warning">${c}<//>`)}
    <//>
    <${B} label="figures">
      <div class="settings-rows">
        <span class="field-label small">Style sheets</span>
        ${(n?.figure_styles??[]).length?r`<${lt} options=${n.figure_styles} value=${l.figure_style??[]} label="Style sheets"
              placeholder="Add a style" onChange=${c=>i("figure_style",c)} />`:r`<span class="muted small"><code>${JSON.stringify(l.figure_style??[])}</code>; choosing others needs the figures
              extra: <code>uv add matplotlib scienceplots</code></span>`}
      </div>
      <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(l.figure_style??[])})</code>, in this order
        (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
        <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <//>
    <${B} label="keyboard">
      <table class="kv">${$t.map(([c,u])=>r`<tr><td><kbd class="small">${c}</kbd></td><td>${u}</td></tr>`)}</table>
    <//>
    <${B} label="about">
      <table class="kv">
        <tr><td class="muted">version</td><td>${n?.version}</td></tr>
        <tr><td class="muted">root</td><td><code class="code">${n?.root}</code></td></tr>
        ${(n?.sources??[]).map(c=>r`
          <tr><td class="muted">${c.name==="."?"local":c.name}</td><td><code class="code">${c.logdir}</code> (${c.kind}, ${c.state})</td></tr>`)}
      </table>
    <//>
  </div></div>`}var $s={system:"light",light:"dark",dark:"system"},Nr={system:"monitor",light:"sun",dark:"moon"};function fs(){let e=D(we),t=D(ge),n=D(te);return r`<header class="topbar">
    <${_} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>te.set(!n)} />
    <a class="project heading" href="/f/local"><${Vn} />${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>ne.set("")} aria-label="Search (⌘K)">
      <${x} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${Pr} />
      <${_} icon=${Nr[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${$s[t]})`}
        onClick=${()=>{Lt("theme_mode",$s[t])}} />
      <a class="icon-button" href=${nt(U.value.page==="group"?U.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${x} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${x} name="settings" size=${16} /></a>
    </div>
  </header>`}function Pr(){let t=(w($e()).data?.meta?.sources??[]).filter(n=>n.name!==".");return t.length?r`${[{name:".",state:"connected"},...t].map(n=>r`<a class=${`source small ${n.state}`}
      href=${E(n.name)}
      data-tip=${n.state==="connected"?`${n.name==="."?"local":n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${x} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name==="."?"local":n.name}</a>`)}`:r`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${x} name="server" size=${15} /> local</span>`}function Rr(e){let[t,n]=y(Date.now());return T(()=>{let s=setInterval(()=>n(Date.now()),e);return()=>clearInterval(s)},[e]),t}function Lr(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function hs(){let e=D(ln),t=D(ae),n=D(cn),s=D(U),o=Rr(5e3),i=w(as()).data,l=L(w(mt()).data),a=D(we),c=i?.daemon,u=i?.runs?.running??0,$=l.filter(C=>C["run.status"]==="failed"&&Lr(C["run.ended_at"])>us).length,d=i?.meta?.freshness,[m,f,b]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&c?["",`live \xB7 updated ${W(new Date(n).toISOString(),o)}`,`beamtime serve, pid ${c.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return r`<footer class="statusbar small">
    <span class="status-item" data-tip=${b}><span class=${`live-dot ${m}`}></span>${f}</span>
    ${u?r`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>ne.set("running")}>
          <${x} name="circle-dot" size=${14} class="tone-accent" />${u} running</button>`:null}
    ${$?r`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>ne.set("failed")}>
          <${x} name="circle-x" size=${14} />${$} failed since your last visit</button>`:null}
    ${d?.behind?r`<span class="status-item warn-text" data-tip=${d.text}><${x} name="hourglass" size=${14} />${d.behind} runs behind</span>`:null}
    ${d?.damaged?.length?r`<span class="status-item warn-text" data-tip=${d.damaged.join(`
`)}><${x} name="triangle-alert" size=${14} />${d.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${s.page==="group"&&s.run?r`<span class="status-item"><${x} name="activity" size=${14} />1 run selected</span>`:null}
    <${_} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>ae.set(!t)} />
    ${a?.outdated?r`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item">${a?.version?`beamtime ${a.version}`:""}</span>
  </footer>`}var gs=null;function ht(e){let t=N(null),[n,s]=y(null),[o,i]=y(!1),[l,a]=y(!1);T(()=>{let d=!0;return gs??=import("./chunks/md-SW3VT2BQ.js"),gs.then(m=>m.render(e.text??"")).then(m=>d&&s(m)),()=>{d=!1}},[e.text]),Jt(()=>{let d=t.current;if(!d||!e.clamp)return;let m=()=>a(d.scrollHeight>d.clientHeight+2),f=new ResizeObserver(m);return f.observe(d),()=>f.disconnect()},[e.clamp,n]);let c=e.clamp&&!o,u=`md${c?" clamped":""}`,$=c?`--clamp:${e.clamp}`:"";return r`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?r`<div class=${u} ref=${t} style=${$}>
          ${(e.text??"").split(/\n{2,}/).map(d=>r`<p>${d}</p>`)}
        </div>`:r`<div class=${u} ref=${t} style=${$} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(l||o)?r`<button type="button" class="link small more" onClick=${()=>i(!o)}>${o?"less":"more"}</button>`:null}
  </div>`}function Ee(e){let[t,n]=y(!!e.startEditing),[s,o]=y(e.value),[i,l]=y(null),[a,c]=y(null),u=N(null),$=N(!1);T(()=>l(null),[e.value]),T(()=>{!t||!u.current||(u.current.focus(),e.startEditing?u.current.select():u.current.setSelectionRange(u.current.value.length,u.current.value.length))},[t]);let[d,m]=y(!1),f=e.locked??void 0,b=g=>{if(!g.target.closest("a, button, input, summary")){if(f)return m(!0);g.preventDefault(),o(i??e.value),c(null),$.current=!1,n(!0)}},C=()=>{$.current=!0,n(!1),c(null),e.onCancel?.()},h=async()=>{if($.current)return;$.current=!0;let g=e.multiline?s.trim():s.replace(/\s*\n\s*/g," ").trim();if(g===e.value.trim()||!g&&!e.multiline)return C();n(!1),l(g);try{await e.onSave(g)}catch(v){l(null),o(g),c(v.message),$.current=!1,n(!0)}},k=g=>{if(g.key==="Escape")return g.preventDefault(),g.stopPropagation(),C();g.key!=="Enter"||g.isComposing||g.keyCode===229||(!e.multiline||g.metaKey||g.ctrlKey)&&(g.preventDefault(),h())};if(t)return r`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${u} class="edit-field" value=${s} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,s.split(`
`).length+1)):1}
        onInput=${g=>o(g.target.value)} onKeyDown=${k} onBlur=${h}></textarea>
      <span class="edit-hint small">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${a?r` · <span class="bad-text">${a}</span>`:null}</span>
    </div>`;let p=i??e.value;return r`<div class=${`editable${f?" locked":""}${i!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${f?`${e.label}: ${f}`:`Edit ${e.label}`}
      data-tip=${f} onClick=${b} onBlur=${()=>m(!1)}
      onKeyDown=${g=>g.key==="Enter"&&g.target===g.currentTarget&&b(g)}>
    ${p.trim()?e.render?e.render(p):p:r`<span class="muted">${e.placeholder??"Click to write"}</span>`}
    ${d&&f?r`<span class="edit-hint small locked-why" role="status"><${x} name="lock" size=${14} /> ${f}</span>`:null}
  </div>`}function It(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function bs({node:e}){let t=Y("proposal"),n=Y("check"),s=t.data,o=n.data;if(!s)return r`<${Q} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let i=s.proposal??{},l=(s.versions??[]).filter(c=>c.version!==s.version),a=!e.props.of||e.props.of===".";return r`<${Q} title="Predictions" result=${t} class="proposal">
    ${a?null:r`<p class="statement">${i.statement}</p>`}
    ${i.rationale?r`<p class="rationale prose">${i.rationale}</p>`:null}
    <${Cn} predictions=${o?.predictions} />
    ${l.length?r`<${Ve} summary=${`${l.length} earlier version${l.length>1?"s":""}`}>
          ${l.map(c=>r`<p class="small"><code>${c.version}</code> ${c.statement}
            <span class="muted">(${c.runs} runs, check ${c.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function vs({node:e}){let t=Y("main"),n=e.data?.main.params.group??".",s=t.data?.chain??[],o=s.find(a=>a.group===n)??null,i=s.filter(a=>a.group!==n),l=o?.notes_since?"out of date":o?`version ${o.versions??1}`:"none yet";return r`<${We} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?l:void 0} open=${!1} result=${t}
      action=${r`<${z} spec=${{icon:"circle-help",tone:"muted",label:_r}} />`}>
    <${Ee} value=${o?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${a=>r`<${ht} text=${a} />`} onSave=${a=>qn(n,a)} />
    ${o&&(o.body?.length>(t.data?.budget??1/0)||o.notes_since>=Ir)?r`<p class="memory-meta small warn-text">${o.body?.length>t.data.budget?`${o.body.length} characters, beyond the budget of ${t.data.budget}`:`${o.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${o?r`<p class="memory-meta small">${o.author} · covers notes until ${o.covers_until?.slice(0,10)}
          ${o.notes_since?r` · <span class="warn-text">${o.notes_since} newer note${o.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${i.length?r`<p class="memory-meta small">Memory above this group: ${i.map((a,c)=>r`${c?", ":""}<a href=${E(a.group)}>${a.group==="."?"local":a.group}</a>`)}</p>`:null}
  <//>`}var Ir=5,_r="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",Or="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function ys({node:e}){let t=Y("main"),n=e.data?.main.params.from??".",s=L(t.data).filter(o=>o.path!==n);return r`<${Q} title=${e.props.title} count=${t.data?String(s.length):void 0} result=${t}>
    ${t.data&&!s.length?r`<${R}>No groups below.<//>`:null}
    <div class="group-list">
      ${s.map(o=>{let[i,l]=It(o.progress),a=(o.failed??0)+(o.killed??0)+(o.lost??0);return r`<a class="group-row" key=${o.path} href=${E(o.path)}
            onPointerEnter=${()=>Ye(o.path)} onFocus=${()=>Ye(o.path)}>
          <${z} spec=${I("research",o.status)} />
          <span class="gname heading">${o.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${o.status!=="concluded"?r`<span class=${`tone-${I("research",o.status).tone}`}>${I("research",o.status).label}</span>`:null}
            ${o.check?r`<${z} spec=${I("result",o.check)} word />`:null}
            ${o.verdict?r`<${z} spec=${I("verdict",o.verdict)} />`:null}
            ${i?r`<span data-tip=${l}>${i}</span>`:null}
            <span class="num"><b>${o.runs}</b> runs</span>
            ${o.running?r`<${z} spec=${I("run","running")} />`:null}
            ${a?r`<span class="tone-bad num" data-tip="failed, killed or lost"><${x} name="circle-x" size=${14} /> ${a}</span>`:null}
          </span>
          ${o.proposal?r`<span class="gstatement caption">${o.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function ws({node:e}){let t=Y("main"),n=e.data?.main.params.from??".",[s,o]=y(!1),i=(t.data?.entries??[]).filter(a=>!String(a.state??"").startsWith("superseded")),l=t.data?.meta?.matched??i.length;return r`<${We} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(l):void 0} result=${t}
      action=${r`<${z} spec=${{icon:"circle-help",tone:"muted",label:Or}} />
        ${r`<${_} icon="plus" label="Add a note" onClick=${()=>o(!0)} />`}`}>
    <div class="notes">
      ${s?r`<${Ar} group=${n} onDone=${()=>o(!1)} />`:null}
      ${t.data&&!i.length&&!s?r`<p class="muted small">No notes yet.</p>`:null}
      ${i.map(a=>r`<${gt} key=${a.id} note=${a} scope=${n} />`)}
      ${t.data?.more&&e.data?r`<${ks} call=${e.data.main} before=${i[i.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var zr=20;function ks(e){let[t,n]=y(!1),s=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:zr}}:null,o=w(s);if(!t)return r`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(o.status==="error")return r`<p class="bad-text small">${o.error}</p>`;let i=o.data?.entries??[];return r`${o.data?null:r`<div class="skeleton" style="block-size: 40px"></div>`}
    ${i.map(l=>r`<${gt} key=${l.id} note=${l} scope=${e.scope} />`)}
    ${o.data?.more?r`<${ks} call=${e.call} before=${i[i.length-1]?.id} scope=${e.scope} />`:null}`}var Br=["observation","decision","idea","question","theory"];function xs(e){return(e?.note_types??Br).filter(t=>t!=="verdict")}function Ar(e){let t=xs(D(we)),[n,s]=y("observation"),[o,i]=y(""),[l,a]=y(""),[c,u]=y(null),[$,d]=y(!1),m=async b=>{if(b.preventDefault(),!o.trim())return u("give the note a title");d(!0);try{await Gn(e.group,n,o.trim(),l.trim()),e.onDone()}catch(C){u(C.message),d(!1)}};return r`<form class="note new-note" onSubmit=${m} onKeyDown=${b=>{b.key==="Escape"&&e.onDone(),b.key==="Enter"&&(b.metaKey||b.ctrlKey)&&m(b)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${n} aria-label="Note type" onChange=${b=>s(b.target.value)}>
        ${t.map(b=>r`<option value=${b}>${b}</option>`)}
      </select></span>
      <span class="input body new-note-field"><input class="new-note-title" value=${o} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${b=>i(b.target.value)} /></span>
    </div>
    <span class="input small"><textarea class="new-note-body" rows="4" value=${l} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${b=>a(b.target.value)}></textarea></span>
    <div class="save-actions">
      <${ee} type="submit" icon=${$?"hourglass":"plus"} disabled=${$}>${$?"Adding\u2026":"Add note"}<//>
      <${ee} icon="x" kind="quiet" onClick=${e.onDone}>Cancel<//>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${c?r`<span class="bad-text small">${c}</span>`:null}
    </div>
  </form>`}function Hr({note:e}){let t=xs(D(we)).filter(n=>n!==e.type);return e.type==="verdict"?r`<span class="sym tone-accent" data-tip="a verdict's type can't change; write a new note">
      <${x} name=${I("note","verdict").icon} size=${15} /></span>`:r`<${it} icon=${I("note",e.type).icon} label="Change the note's type" title="Note type">
    <div class="menu-list">
      ${t.map(n=>r`<button type="button" key=${n} onClick=${()=>ut(e,{type:n})}>
        <${x} name=${I("note",n).icon} size=${15} /> ${n}</button>`)}
    </div>
  <//>`}function gt(e){let t=e.note,[n,s]=y(!!e.open),[o,i]=y(!1),l=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,a=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),c=t.meta?.author;return r`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${u=>!u.target.closest(".editable, a, .note-delete, .popover-wrap")&&s(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${x} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${Hr} note=${t} />
      <${Ee} value=${t.description} label="the note's title" class="note-title prose" render=${Ur}
        onSave=${u=>ut(t,{description:u})} />
      ${t.overall?r`<${z} spec=${I("verdict",t.overall)} />`:null}
      ${t.state?r`<${Se} tone="warn">${t.state}<//>`:null}
      ${l?r`<a class="note-group small" href=${E(l)} data-tip="from this group">${Kr(l,e.scope)}</a>`:null}
      <span class="note-meta small">${c?`${c} \xB7 `:""}${W(a)}</span>
      ${r`<${_} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${o}
        onClick=${u=>{u.stopPropagation(),i(!o)}} />`}
    </div>
    ${o?r`<div class="note-confirm small" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <${ee} icon="trash" kind="danger" onClick=${()=>{Yn(t)}}>Delete<//>
          <${ee} icon="x" kind="quiet" onClick=${()=>i(!1)}>Cancel<//>
        </div>`:null}
    ${n?r`<${Ee} value=${t.body??""} label="the note" multiline class="note-body prose markdown"
          placeholder="Add details in Markdown" render=${u=>r`<${ht} text=${u} />`}
          onSave=${u=>ut(t,{body:u})} />`:null}
  </article>`}function Kr(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,s=n.split("/").pop()??n;return ie(s)?s.slice(-8):n}function Cs({node:e}){let t=Y("main"),n=t.data?.lines??[],s=t.data?.meta??{},o=r`<${x} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${s.total_lines??n.length} lines${(s.shown??0)<(s.total_lines??0)?`, last ${s.shown}`:""}`:""}</span>`;return r`<${Q} result=${t}>
    <${Ve} summary=${o} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function Ss({node:e}){let t=J(F);return r`<${Q} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${Ee} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${_e.value===e.id} onCancel=${()=>_e.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>r`<${ht} text=${n} />`}
      onSave=${n=>(_e.set(null),dt(t.path,e.id,n))} />
  <//>`}function Es({node:e}){return r`<${R} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function Ur(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let s=n.slice(2,-2),[o]=s.split(/[#@]/),i=o.split("/").pop()??"";return r`<a href=${ie(i)?oe(i):E(o)}>${s}</a>`}return n.startsWith("`")?r`<code>${n.slice(1,-1)}</code>`:n})}function Fr(e,t){let n=/^(?:ssh|https?|git):\/\/(?:[^@/]*@)?([^/:]+)(?::\d+)?\/(.+?)(?:\.git)?\/?$/.exec(e??""),s=/^(?:[^@/]+@)?([^/:]+):(?!\/)(.+?)(?:\.git)?\/?$/.exec(e??""),[,o,i]=n??s??[];return!o||!i?null:o==="github.com"?{host:"GitHub",url:`https://github.com/${i}/commit/${t}`}:o==="gitlab.com"||o.startsWith("gitlab.")?{host:"GitLab",url:`https://${o}/${i}/-/commit/${t}`}:null}function bt(e){let{git:t,copied_from:n}=e.run,s=[];return t?.commit&&s.push(["code",r`<${Wr} git=${t} />`]),n&&s.push(["copied from",r`<a href=${oe(n.id)} data-tip=${`${n.id}, ${n.at}`}>${n.path??n.id}</a>`]),e.checkpoints?.length&&s.push(["checkpoints",r`${e.checkpoints.map(o=>r`<${jr} key=${o.name} ck=${o} />`)}`]),s}function Wr({git:e}){let t=Fr(e.remote,e.commit);return r`<span>${e.commit.slice(0,10)}${e.branch?r` on ${e.branch}`:null}
    ${e.dirty?r` <${Se} tone="warn" tip="Uncommitted changes when the run started">dirty<//>`:null}
    ${t?r` · <a href=${t.url} target="_blank" rel="noopener noreferrer">${t.host}</a>`:null}</span>`}function jr({ck:e}){let t=()=>{navigator.clipboard?.writeText(e.location)};return r`<div class="checkpoint">
    <span class=${e.exists?"":"muted"} data-tip=${e.location??void 0}>${e.name}</span>
    ${e.exists?null:r`<${Se} tone="warn" tip=${e.location??void 0}>missing<//> <span class="muted">${Vr(e)}</span>`}
    ${e.location?r`<${_} icon="copy" label=${`Copy the path of ${e.name}`} onClick=${t} />`:null}
  </div>`}function Vr(e){return e.location?e.via==="origin"?"not found where the source run kept it":"not found at its recorded location":"no location recorded"}function vt({run:e,scope:t}){let[n,s]=y(!1),o=w(n?ss(e,t):null);return r`<${Ve} summary="Uncommitted changes" onToggle=${s}>
    ${o.error?r`<p class="muted small">${o.error}</p>`:null}
    ${o.data?r`<pre class="log code diff">${String(o.data.text).split(`
`).map(i=>r`<span class=${Gr(i)}>${i}\n</span>`)}</pre>`:n&&!o.error?r`<div class="skeleton late" style="block-size: 80px"></div>`:null}
  <//>`}function Gr(e){return e.startsWith("+++")||e.startsWith("---")||e.startsWith("@@")?"muted":e.startsWith("+")?"tone-good":e.startsWith("-")?"tone-bad":""}function Ts(e){let t=()=>P(E(e.path),{replace:!0});return r`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${x} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${_} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?r`<${qr} id=${e.run} scope=${e.path} />`:r`<${Xr} path=${e.path} />`}
  </aside>`}function qr({id:e,scope:t}){let n=w(ze(e,t)).data,s=w(ns(e,t)).data,o=w(Xe(t)).data,i=w({method:"keys",params:{from:t},scope:t}).data,l=me(),a=Te(()=>ot(L(o).map(m=>m["run.id"]),l).get(e),[o,l,e]);if(!n)return r`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let c=n.run,u=Object.entries(n.metrics??{}),$=hn(a,l),d=bt(n);return r`<div class="drawer-body">
    <h3 class="heading"><span class=${$.class} style=${$.style}></span>
      <a href=${oe(e)}>${c.name}</a></h3>
    <p class="facts small">
      <${z} spec=${Ge(c.status,c.exit)} word tip=${et(c)} />
      <span><b>${de(c.steps)}</b> steps</span>
      <span><b>${Me(c.duration_s)}</b></span>
      <span data-tip=${c.created_at}>${W(c.created_at)}</span>
    </p>
    ${c.error?r`<pre class="log code bad-text">${c.error}</pre>`:null}
    ${d.length?r`<table class="kv small">${d.map(([m,f])=>r`<tr><td class="muted">${m}</td><td>${f}</td></tr>`)}</table>`:null}
    ${c.git?.dirty?r`<${vt} run=${c.id} scope=${t} />`:null}
    <h4 class="small">Config</h4>
    <${ct} config=${n.config??{}} varying=${qe(i)} />
    ${u.length?r`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${u.map(([m,f])=>r`<tr><td>${m}</td><td class="num"><b>${G(f.last)}</b></td>
              <td class="num">${G(f.min)}</td><td class="num">${G(f.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?r`<h4 class="small">Cited by</h4>${n.cited_by.map(m=>r`<p class="small"><${z} spec=${I("note",m.type)} /> ${m.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(m=>r`<div class="event small"><span class="muted num">${m.t?.slice(5,16).replace("T"," ")}</span>
        <${x} name=${Et(m.type)} size=${14} /><span>${m.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(s?.lines??[]).join(`
`)}</pre>
  </div>`}function Xr({path:e}){let t=w(pt(e)).data,n=w(os(e)).data;return r`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?r`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(s=>!String(s.state??"").startsWith("superseded")).map(s=>r`<${gt} key=${s.id} note=${s} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(s=>r`<div class="event small"><span class="muted num">${s.t?.slice(5,16).replace("T"," ")}</span>
        <${x} name=${s.kind==="note"?"file-text":Et(s.type)} size=${14} />
        <span>${s.run?r`<a href=${oe(s.run)}>${s.run.slice(-8)}</a> `:null}${s.description??s.type}</span></div>`)}
  </div>`}function yt(e,t){let n=w(e),s=N(null);return n.status!=="loading"&&(s.current={scope:t,result:n}),n.status==="loading"&&s.current?.scope===t?s.current.result:n}var _t=null;function Ms(e){_t?.();let t=document.querySelector(".main");if(!e||!t)return;let n=e.getBoundingClientRect().top,s=new ResizeObserver(()=>{e.isConnected&&(t.scrollTop+=e.getBoundingClientRect().top-n)});for(let a of t.children)s.observe(a);let o=["wheel","touchmove","keydown","pointerdown"],i=()=>{s.disconnect(),clearTimeout(l);for(let a of o)removeEventListener(a,i);_t=null},l=setTimeout(i,5e3);for(let a of o)addEventListener(a,i,{passive:!0});_t=i}var Ot=["failed","killed","lost"],Yr={icon:"eye-off",tone:"muted",label:"Hidden"},Zr="Hidden: left out of tables, counts and checks until promoted";function zt(e){let t=De(e.path),n=t==="."?e.path:e.path.slice(t.length+1),s=X(e.path)?[]:n.split("/"),o=s.length&&ie(s[s.length-1])?s[s.length-1]:null,i=s.slice(0,-1),l=a=>[...t==="."?[]:[t],...i.slice(0,a+1)].join("/");return r`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${s.length?r`<a href=${E(t)}>${t==="."?"local":t}</a>`:null}
      ${i.map((a,c)=>r`<span>/</span><a href=${E(l(c))}>${a}</a>`)}
    </nav>
    ${o?r`<${eo} id=${o} scope=${e.path} />`:r`<${Jr} path=${e.path} />`}
    ${e.finding?r`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function Jr({path:e}){let t=L(w(Oe(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return r`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let s=D(U),o=s.page==="group"&&s.hiddenRuns,i=Object.entries(w({method:"keys",params:{from:e},scope:e}).data?.codes??{}),l=Ot.reduce((a,c)=>a+(t[c]??0),0);return r`
    <h1 class="page-title title" tabindex="-1">${n} <${z} spec=${I("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?r`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?r`<span><b>${t.finished}</b> finished</span>`:null}
      ${l?r`<span class="tone-bad" data-tip=${Ot.filter(a=>t[a]).map(a=>`${t[a]} ${a}`).join(", ")}>
            <${x} name="circle-x" size=${15} /> <b>${l}</b> ${l===1?Ot.find(a=>t[a]):"ended early"}</span>`:null}
      ${i.length?r`<span data-tip=${i.map(([a,c])=>`${a}: ${c} run${c===1?"":"s"}`).join(", ")}>
            <${x} name="git-commit" size=${15} /> <b>${i.length}</b> code versions</span>`:null}
      ${t.hidden?r`<span><a href=${E(e,{hidden:!o})} data-tip=${o?"Close the list of hidden runs":"List the hidden runs"}>
            <${x} name="eye-off" size=${15} /> <b>${t.hidden}</b> hidden</a></span>`:null}
      ${t.notes?r`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${Ps} path=${e} />
    </p>`}function Ds({path:e}){let t=L(w(rs(e)).data);return t.length?r`<${B} label="hidden runs">
    <table class="runs">
      <thead><tr class="small"><th>run</th><th>status</th><th>created</th><th></th></tr></thead>
      <tbody>${t.map(n=>r`<tr key=${n["run.id"]}>
        <td><a href=${oe(n["run.id"],e)}>${n["run.name"]??n["run.id"]}</a></td>
        <td><${z} spec=${Ge(n["run.status"],null)} word /></td>
        <td class="muted" data-tip=${n["run.created_at"]}>${W(n["run.created_at"])}</td>
        <td><${ee} icon="eye" kind="quiet" onClick=${()=>Pt(n["run.id"],e)}>Promote<//></td>
      </tr>`)}</tbody>
    </table>
  <//>`:null}function Ns({path:e}){let t=L(w(Oe(e)).data)[0]??null,n=w(t?.proposal?es(e):null).data,s=w(t?.proposal?ts(e):null).data;if(!t?.proposal)return null;let o=s?.proposal?.rationale,i=s?.versions?.find(c=>c.version===s.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[l,a]=It(n?.progress?.text??t.progress);return r`<${B} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${Ee} value=${t.proposal} label="the proposal's statement" locked=${s?i:"Loading the proposal\u2026"}
          render=${c=>r`<span data-tip=${i?void 0:o}>${c}</span>`}
          onSave=${c=>Xn(e,c)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(c=>{let u=I("result",c.result),$=xn(c),d=$?`${u.label}: ${$}`:u.label;return r`<span class=${`check small tone-${u.tone}`} key=${c.name} data-tip=${d}
              aria-label=${`${c.name}: ${d}`} tabindex="0"><${x} name=${u.icon} size=${14} />${c.name}</span>`})}
        ${n?.provisional||l?r`<span class="small">
              ${n?.provisional?r`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${l?r`<span class="muted" data-tip=${a}>${n?.provisional?" \xB7 ":""}${l}</span>`:null}
            </span>`:null}
      </div>
      <${Qr} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function Qr(e){let t=w(e.verdict?pt(e.path):null).data;if(!e.verdict)return r`<p class="verdict-line muted">no verdict yet</p>`;let n=I("verdict",e.verdict),s=(t?.entries??[]).find(i=>i.type==="verdict"&&(i.group??e.path)===e.path),o=s?ke(s.id):null;return r`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${x} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${s?r`<span class="small muted" data-tip=${o}>verdict${s.meta?.author?` by ${s.meta.author}`:""}${o?` \xB7 ${W(o)}`:""}</span>`:null}
  </p>`}function eo({id:e,scope:t}){let n=w(ze(e,t)).data;if(!n)return r`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let s=n.run,o=()=>{navigator.clipboard?.writeText(s.id)},i=()=>{Pt(s.id,t)};return r`
    <h1 class="page-title title" tabindex="-1"><${Ee} value=${s.name??s.id} label="the run's name" class="title-edit"
        onSave=${l=>Zn(s.id,t,l.trim())} />
      <${z} spec=${Ge(s.status,s.exit)} word tip=${et(s)} />
      ${s.hidden?r`<${z} spec=${Yr} word tip=${Zr} />`:null}</h1>
    ${s.error?r`<p class="bad-text" data-tip=${s.error}>${s.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${de(s.steps)}</b> steps</span>
      <span><b>${Me(s.duration_s)}</b></span>
      ${n.progress?r`<${to} run=${s} progress=${n.progress} />`:null}
      <span data-tip=${s.created_at}>${W(s.created_at)}</span>
      <${Ps} path=${t} />
      ${s.hidden?r`<${_} icon="eye" label="Promote: count this run in tables, charts and checks" onClick=${i} />`:null}
      <${_} icon="copy" label=${`Copy the run id ${s.id}`} onClick=${o} />
      <${it} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${[...no(s),...bt(n)].map(([l,a])=>r`<tr><td class="muted">${l}</td><td>${a}</td></tr>`)}</table>
        ${s.git?.dirty?r`<${vt} run=${s.id} scope=${t} />`:null}
        <div class="menu-list">
          <button type="button" onClick=${()=>P(E(t,{run:s.id}),{replace:!0})}>
            <${x} name="panel-right" size=${15} /> Open in the side panel</button>
          ${s.hidden?r`<button type="button" onClick=${i}><${x} name="eye" size=${15} /> Promote</button>`:null}
          <button type="button" onClick=${o}><${x} name="copy" size=${15} /> Copy the run id</button>
          ${s.git?.commit?r`<button type="button" onClick=${()=>navigator.clipboard?.writeText(s.git.commit)}>
            <${x} name="git-commit" size=${15} /> Copy the commit</button>`:null}
        </div>
      <//>
    </div>
    ${(n.proposals??[]).length?r`<div class="checks">
          ${n.proposals.map(l=>{let a=I("result",l.check);return r`<a class=${`check small tone-${a.tone}`} href=${E(l.group)} data-tip=${l.statement}>
              <${x} name=${a.icon} size=${14} />${l.group==="."?"own proposal":l.group}
              ${l.verdict?r`<${z} spec=${I("verdict",l.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function to({run:e,progress:t}){let{epoch:n,total:s,fraction:o,steps_per_epoch:i}=t,l=e.status==="running"&&o!==null&&i&&e.steps_per_s?Me((1-o)*s*i/e.steps_per_s):null;return r`<span>epoch <b>${n}</b>${s?` of ${s}`:""}${o===null?"":` \xB7 ${Math.round(o*100)} % through`}${l?` \xB7 about ${l} left`:""}</span>`}function Ps({path:e}){let t=re(e).main,n=yt(Rt(e,t),e).data?.summary;if(!n)return null;let s=Object.entries(n.config??{}).map(([l,a])=>`${xe(l)} ${G(a)}`).join(", "),o=ie(e.split("/").pop()??""),i=`${n.stat} of ${n.metric} over ${o?"the run":"all runs"}${s?` (${s})`:""}`;return r`<span data-tip=${i}>
    best <b>${n.label??xe(`metric.${n.metric}.${n.stat}`)} ${G(n.value)}</b>
    ${o?null:r` · <a href=${oe(n.run)}>${n.name}</a>`}
  </span>`}function no(e){return[["id",e.id],["host",e.host],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,s])=>[n,String(s)])}var Bt=80;function Rs({node:e}){let t=Y("main"),n=Y(e.data?.keys?"keys":""),s=e.props.mode==="run",o=e.props.title??(s?"Config":"Hyperparameters");return r`<${We} id=${`config:${e.id}`} title=${o} open=${e.props.open} result=${t}>
    ${t.data?s?r`<${ct} config=${t.data.config} varying=${qe(n.data)} />`:r`<${so} rows=${t.data.config?.rows??[]} />`:r`<div class="skeleton late" style="block-size: 80px"></div>`}
  <//>`}function so({rows:e}){let t=new Set(qe({config:{rows:e}})),n=e.filter(([s])=>t.has(s.replace(/^config\./,"")));return n.length?r`<table class="kv small">${n.map(([s,,o])=>{let i=Array.isArray(o)?o.map(G).join(", "):`${G(o.min)} \u2026 ${G(o.max)} \xB7 ${o.distinct} values`;return r`<tr><td data-tip=${s}>${s.replace(/^config\./,"")}</td>
      <td data-tip=${i.length>Bt?i:void 0}>${i.length>Bt?`${i.slice(0,Bt-1)}\u2026`:i}</td></tr>`})}</table>`:r`<p class="muted small">No config differs between the runs.</p>`}var Ls=15e3;function Is({node:e}){let t=J(F),n=me(),[s,o]=yn(),i=e.props.code,l=w(o&&i?{method:"code",params:i,scope:null}:null),[a,c]=y(null),[u,$]=y(120),[d,m]=y({error:null,warnings:[]}),f=k=>{le&&console.error(`[block ${e.id}] ${k}`),m(p=>({...p,error:k}))},b=N(()=>{});T(()=>{if(!a)return;m(v=>v.own?{...v,own:!1}:v);let k=!0;Ke.n++;let p=()=>{k&&Ke.n--,k=!1};b.current=p;let g=setTimeout(()=>{k&&f(`no first render within ${Ls/1e3} s`),p()},Ls);return()=>{clearTimeout(g),p()}},[a]),T(()=>{let k=a?.contentWindow;if(!k||l.status!=="ready")return;let p=M=>k.postMessage(M,"*"),g=new Map,v=new Dn,A=M=>{if(M.source!==k)return;let S=M.data;switch(S.type){case"hello":p({type:"init",init:{id:e.id,code:l.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:vn.value,pair:st.value,colormaps:Fe.value,prefs:Ae(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics,expanded:e.props.expanded?Sn():null}});break;case"sub":if(!En.has(S.call.method)){p({type:"result",id:S.id,result:{status:"error",data:null,error:`${S.call.method} is not available in a custom block`,refreshing:!1}});break}g.get(S.id)?.(),g.set(S.id,an(S.call,se=>p({type:"result",id:S.id,result:se})));break;case"unsub":g.get(S.id)?.(),g.delete(S.id);break;case"navigate":S.url.startsWith("/")&&P(S.url);break;case"height":v.accept(performance.now())?$(Math.max(40,S.height)):H("its height keeps changing, so it is fixed at its last height");break;case"chrome":m(se=>({...se,own:S.own}));break;case"ready":m(se=>({...se,blank:S.blank,overflow:S.overflow})),b.current();break;case"warn":H(S.message);break;case"hover":Ne.set(S.run);break;case"prefs":JSON.stringify(K.value)!==JSON.stringify(S.prefs)&&K.set(S.prefs);break;case"download":case"snapshot":S.href?Tn(S.href,S.name)?performance.now()-V>1e3&&(V=performance.now(),be().download(S.href,S.name)):H(`a download of ${S.name} was refused: only PNG, SVG and CSV files`):H("it draws no SVG or canvas to download");break;case"figure":be().figure(S.spec,S.name).catch(se=>H(`the PDF failed: ${se.message}`));break;case"expand":Mn(S.node)&&be().expand(S.node,t);break;case"expand-block":e.props.expanded||be().expand(e,t);break;case"close":e.props.expanded&&Ie.set(null);break;case"error":f(S.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,C)),b.current();break;default:break}},H=M=>{le&&console.warn(`[block ${e.id}] ${M}`),m(S=>S.warnings.includes(M)?S:{...S,warnings:[...S.warnings,M]})},V=-1/0,K=Ae(t.path),q=Ne.subscribe(M=>p({type:"hover",run:M})),O=K.subscribe(M=>p({type:"prefs",prefs:M}));return addEventListener("message",A),p({type:"ping"}),()=>{q(),O(),removeEventListener("message",A);for(let M of g.values())M()}},[l.status,l.data?.code,a]),T(()=>{let k={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};a?.contentWindow?.postMessage(k,"*")},[t.names,t.colors,t.metrics,a]),T(()=>Fe.subscribe(k=>a?.contentWindow?.postMessage({type:"colormaps",colormaps:k},"*")),[a]),T(()=>{n&&a?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let C=typeof i=="object"?i.path??i.block:String(i??"");wn(e.id,{png:()=>a?.contentWindow?.postMessage({type:"snapshot"},"*")});let h=o&&l.status==="ready"&&!d.error;return r`<div ref=${s} class="custom-block">
    ${d.own?null:r`<div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${h?r`<span class="chart-tools">
            <${_} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>a?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?r`<${_} icon="x" label="Close (Esc)" onClick=${()=>Ie.set(null)} />`:r`<${_} icon="maximize" label="Expand" onClick=${()=>be().expand(e,t)} />`}
          </span>`:null}
    </div>`}
    <${Q} caption=${e.props.expanded?void 0:e.props.caption} result=${l}>
      ${d.error?r`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${C})</span>
            <pre class="code">${d.error}</pre>
          </div>`:null}
      ${d.warnings.map(k=>r`<${R} kind="warning">${k}<//>`)}
      ${h?r`<div class="custom-frame" data-frame-blank=${d.blank?"1":void 0} data-frame-overflow=${d.overflow?"1":void 0}>
            <iframe key=${l.data.code} ref=${c} sandbox="allow-scripts" ...${ro()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${u}px`} />
          </div>`:null}
    <//>
  </div>`}function ro(){if(!!1)return{src:Qt("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1"),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}function _s({node:e}){let t=Y("main"),n=e.props,s=t.data,o=s?Ln(s.rows):[],i=s?.meta?.matched,l=`Each field is rated on its own, so interactions between fields are not shown${i===void 0?"":`; the measures rest on ${i} finished run${i===1?"":"s"}`}.`;return r`<${Q} title=${n.title} caption=${n.caption} result=${t}>
    ${s?s.notice?r`<${R}>${s.notice}<//>`:o.length?r`<div class="table-wrap"><table class="runs importance">
              <thead><tr class="small">
                <th data-tip=${s.target}>${xe(s.target)}</th>
                <th class="num" data-tip="Spearman rank correlation with the target; the bar is its magnitude, a minus means the target falls as the field rises">rank correlation</th>
                <th class="num" data-tip="share of the target's variance explained by grouping on the field (η², numeric fields in quantile bins)">variance explained</th>
                <th class="num" data-tip="runs that set the field">runs</th>
              </tr></thead>
              <tbody>
                ${o.map(a=>r`<tr key=${a.field}>
                    <td data-tip=${a.field}>${xe(a.field)}</td>
                    <td class="num progress" data-tip=${a.rho===null?"not a numeric field":void 0}>${Dt(a.rho)}<span class="bar" style=${`--fraction: ${a.rhoFraction}`}></span></td>
                    <td class="num progress">${Dt(a.eta)}<span class="bar" style=${`--fraction: ${a.etaFraction}`}></span></td>
                    <td class="num">${a.n}</td>
                  </tr>`)}
              </tbody>
            </table></div>`:r`<${R}>No config field varies across these runs.<//>`:r`<div class="skeleton late" style="block-size: 120px"></div>`}
    ${o.length&&!s?.notice?r`<p class="caption">${l}</p>`:null}
  <//>`}function At(e,t){let n=e?.steps??[];if(t==="step")return{values:n,steps:n};let s=new Map;n.forEach((i,l)=>{let a=e?.clocks?.[l];a!=null&&Number.isFinite(a)&&s.set(a,Math.max(s.get(a)??i,i))});let o=[...s.keys()].sort((i,l)=>i-l);return{values:o,steps:o.map(i=>s.get(i))}}function Ht(e){return At(e,"clock").values.length>1}function Os(e,t){let n=0;return e.forEach((s,o)=>{Math.abs(s-t)<Math.abs(e[n]-t)&&(n=o)}),n}function zs(e,t){let n=0;return e.steps.forEach((s,o)=>{s<=t&&(n=o)}),n}function Bs(e,t){let n=new Map;for(let s of e)s.step<=t&&s.step>(n.get(s.run)??-1/0)&&n.set(s.run,s.step);return e.filter(s=>n.get(s.run)===s.step).map(s=>({entry:s,earlier:s.step<t&&t!==1/0}))}function As(e){return e.reduce((t,n)=>!t||n.entry.step>t.entry.step?n:t,void 0)}function Hs(e,t,n){let s=e?.split(/[/.]/).at(-1);return[...s&&s!=="step"&&t!=null?[`${s} ${G(t)}`]:[],`step ${de(n)}`].join(" \xB7 ")}function Ks(e,t){let n=e?.steps?.indexOf(t)??-1;return n<0?null:e?.clocks?.[n]??null}var Kt={k:1,x:0,y:0},Us=32;function Fs(e,t,n){let s=Math.min(Us,Math.max(1,e.k));return{k:s,x:Math.min(0,Math.max(t*(1-s),e.x)),y:Math.min(0,Math.max(n*(1-s),e.y))}}function oo(e,t,n,s,o,i){let l=Math.min(Us,Math.max(1,e.k*t)),a=l/e.k;return Fs({k:l,x:n-(n-e.x)*a,y:s-(s-e.y)*a},o,i)}function ao(e,t,n,s,o){return Fs({...e,x:e.x+t,y:e.y+n},s,o)}function Ws(e){return`translate(${e.x}px, ${e.y}px) scale(${e.k})`}function js(){let e=N(null),[t,n]=y(Kt),s=()=>{let a=e.current.getBoundingClientRect();return{w:a.width,h:a.height,left:a.left,top:a.top}},o=(a,c)=>{let{w:u,h:$}=s();n(d=>oo(d,a,c?.x??u/2,c?.y??$/2,u,$))};T(()=>{let a=e.current;if(!a)return;let c=u=>{u.preventDefault();let{left:$,top:d}=s();o(Math.exp(-u.deltaY*(u.ctrlKey?.01:.002)),{x:u.clientX-$,y:u.clientY-d})};return a.addEventListener("wheel",c,{passive:!1}),()=>a.removeEventListener("wheel",c)},[]);let i=N(new Map);return{box:e,pose:t,handlers:{onPointerDown:a=>{a.currentTarget.setPointerCapture(a.pointerId),i.current.set(a.pointerId,{x:a.clientX,y:a.clientY})},onPointerMove:a=>{let c=i.current.get(a.pointerId);if(!c)return;let u={x:a.clientX,y:a.clientY},{w:$,h:d,left:m,top:f}=s(),b=[...i.current.entries()].filter(([C])=>C!==a.pointerId).map(([,C])=>C);if(i.current.set(a.pointerId,u),b.length){let[C]=b,h=Math.hypot(c.x-C.x,c.y-C.y),k=Math.hypot(u.x-C.x,u.y-C.y);h>0&&o(k/h,{x:(u.x+C.x)/2-m,y:(u.y+C.y)/2-f})}else n(C=>ao(C,u.x-c.x,u.y-c.y,$,d))},onPointerUp:a=>{i.current.delete(a.pointerId)},onPointerCancel:a=>{i.current.delete(a.pointerId)},onDblClick:()=>n(Kt)},zoomBy:o,fit:()=>n(Kt)}}var Ut=new Map;function io(e,t){return Ut.has(e)||Ut.set(e,new fe({step:t,by:"step"})),Ut.get(e)}function lo(e,t,n){let s=N(e),[,o]=y(0);return n&&(s.current=e),T(()=>{if(n||s.current===e)return;let i=setTimeout(()=>{s.current=e,o(l=>l+1)},t);return()=>clearTimeout(i)},[e,n]),s.current}function co(e){let t=J(F),n=e.data.main,s=n.params.step,o=`${t.path}\0${e.id}`,i=io(o,typeof s=="number"?s:null),l=D(i),a=w(n),c=a.data?.meta,u=l.by==="clock"&&Ht(c)?"clock":"step",$=Te(()=>At(c,u),[c,u]),d=l.step===null,m=!(le||!1)&&(s==="last"||typeof s=="number")&&$.steps.length>1,f=M=>M===null?$.steps.length-1:zs($,M),b=f(l.step),C=$.steps[b]??0,h=N(null),k=lo(l.step,120,!h.current),p=$.steps[f(k)]??0,g=m&&(!d||s!=="last"),v=g?{...n,params:{...n.params,step:["last",p],limit:2e3}}:null,A=w(v),H=g?A.data:a.data;H&&(h.current={entries:H.entries,at:g?p:1/0});let V=s!=="last"&&typeof s!="number",K=h.current?V?h.current.entries.map(M=>({entry:M,earlier:!1})):Bs(h.current.entries,h.current.at):[],q=n.params.clock??null,O=M=>{let S=Math.min($.steps.length-1,Math.max(0,M));i.set({...l,step:S===$.steps.length-1?null:$.steps[S]})};return{view:t,base:a,error:A.status==="error"?String(A.error):null,tiles:K,stops:$,i:b,ranged:m,by:u,move:O,clock:q,label:Hs(q,Ks(c,C),C),clocked:Ht(c),setBy:M=>i.set({step:d?null:C,by:M})}}function uo(e,t,n){let s=t.path.split(".").at(-1);return[Qe(pe(t.run,e.path),t.path),`${t.run}-${n.replace(/[^\w.-]+/g,"_")}-step${t.step}.${s}`]}function Vs(e,t,n){for(let{entry:s}of t)be().download(...uo(e,s,n))}function Gs(e,t,n,s){return{files:[{label:s,save:()=>n&&Vs(e.view,[n],t)},{label:`All images (${e.tiles.length})`,save:()=>Vs(e.view,e.tiles,t)}]}}function qs({s:e}){if(!e.ranged)return null;let{values:t}=e.stops,n={ArrowLeft:e.i-1,ArrowDown:e.i-1,ArrowRight:e.i+1,ArrowUp:e.i+1,Home:0,End:t.length-1};return r`<div class="scrubber">
    <input type="range" min=${t[0]} max=${t.at(-1)} step="any" value=${t[e.i]} aria-label="Step" aria-valuetext=${e.label}
      onInput=${s=>{let o=s.target,i=Os(t,Number(o.value));o.value=String(t[i]),e.move(i)}}
      onKeyDown=${s=>{s.key in n&&(s.preventDefault(),e.move(n[s.key]))}} />
    <span class="small scrub-label">${e.label}</span>
  </div>`}function Xs({s:e}){if(!e.ranged||!e.clocked)return null;let t=e.clock?.split(/[/.]/).at(-1)??"clock";return r`<button type="button" class="small tool-toggle" aria-pressed=${e.by==="clock"} data-tip=${`Space the stops by ${t}`}
    onClick=${()=>e.setBy(e.by==="clock"?"step":"clock")}>by ${t}</button>`}function Ys({node:e}){let t=co(e),n=String(e.props.title??e.data.main.params.key);if(e.props.expanded)return r`<${po} node=${e} s=${t} title=${n} />`;let s=o=>be().expand({...e,props:{...e.props,run:o??t.tiles[0]?.entry.run}},t.view);return r`<div class="block chart-block images-block">
    <${Mt} id=${e.id} title=${n} caption=${e.props.caption}
      tools=${r`<${Xs} s=${t} />`}
      downloads=${Gs(t,n,As(t.tiles),"Latest image")} onExpand=${()=>s()}>
      ${t.base.status==="error"?r`<${R} kind="error">${t.base.error}<//>`:null}
      ${t.error?r`<${R} kind="error">${t.error}<//>`:null}
      ${t.base.data&&!t.tiles.length?r`<${R}>No images logged.<//>`:null}
      <div class="images">
        ${t.tiles.map(({entry:o,earlier:i})=>r`<figure key=${`${o.run}/${o.path}`} class=${i?"earlier":""} data-tip=${t.view.names.get(o.run)??o.run}>
            <button type="button" class="image-open" aria-label="Open larger" onClick=${()=>s(o.run)}>
              <img src=${Qe(pe(o.run,t.view.path),o.path)} alt=${o.caption??n} loading=${Ue?"eager":"lazy"} />
            </button>
            <figcaption class="small">step ${de(o.step)}${o.caption?` \xB7 ${o.caption}`:""}</figcaption>
          </figure>`)}
      </div>
      <${qs} s=${t} />
    <//>
  </div>`}function po({node:e,s:t,title:n}){let{tiles:s}=t,[o,i]=y(e.props.run),l=js(),a=Math.max(0,s.findIndex(f=>f.entry.run===o)),c=s[a],u=c?Qe(pe(c.entry.run,t.view.path),c.entry.path):"";T(()=>l.fit(),[u]);let $=f=>i(s[(a+f+s.length)%s.length].entry.run),d={"+":()=>l.zoomBy(1.5),"=":()=>l.zoomBy(1.5),"-":()=>l.zoomBy(1/1.5),0:l.fit},m=r`
    ${s.length>1?r`<${_} icon="chevron-left" label="Previous image" onClick=${()=>$(-1)} /><${_} icon="chevron-right" label="Next image" onClick=${()=>$(1)} />`:null}
    <${_} icon="minus" label="Zoom out (−)" onClick=${()=>l.zoomBy(1/1.5)} />
    <${_} icon="plus" label="Zoom in (+)" onClick=${()=>l.zoomBy(1.5)} />
    <${_} icon="reset" label="Fit (double-click, 0)" onClick=${l.fit} />
    <${Xs} s=${t} />`;return r`<div class="block chart-block images-block">
    <${Mt} id=${e.id} title=${n} expanded
      notes=${c?[t.view.names.get(c.entry.run)??c.entry.run,`step ${de(c.entry.step)}`]:[]}
      tools=${m} downloads=${Gs(t,n,c,"This image")}>
      <div class="zoom-box" ref=${l.box} tabindex="0" style=${{touchAction:"none"}} ...${l.handlers}
        onKeyDown=${f=>d[f.key]?.()}>
        ${c?r`<img class="zoom-img" src=${u} alt=${c.entry.caption??n} draggable=${!1} style=${{transform:Ws(l.pose)}} />`:null}
      </div>
      <${qs} s=${t} />
    <//>
  </div>`}function Zs({node:e}){let t=Y("main"),n=t.data?.entries??[];return r`<${Q} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?r`<${R}>No text logged.<//>`:null}
    ${n.map(s=>r`<div class="text-entry" key=${`${s.run}/${s.step}`}>
        <div class="muted small">step ${de(s.step)}${s.caption?` \xB7 ${s.caption}`:""}</div>
        <pre class="code">${s.text??""}</pre>
      </div>`)}
  <//>`}function Js({node:e}){let n=`section.${J(F).path}:${e.id}`,[s,o]=y(()=>Ue||Ce(n,e.props.open!==!1)),i=()=>{he(n,!s),o(!s)},l=r`${(e.children??[]).map(u=>r`<${ue} key=${u.id} node=${u} />`)}`,a=J(at);if(!e.props.title)return r`<div class="stack">${l}</div>`;let c=a===e.props.title.toLowerCase();return r`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${s} aria-label=${c?`${s?"Close":"Open"} ${e.props.title}`:void 0}
        data-tip=${c?`${s?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${i}>
      <${x} name=${s?"chevron-down":"chevron-right"} size=${16} />${c?r`<span class="toggle-label code">${a}</span>`:e.props.title}
    </button>
    ${s?r`<div class="stack">${l}</div>`:null}
  </div>`}function Qs({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return r`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>r`<${ue} key=${n.id} node=${n} />`)}
  </div>`}function Wt({node:e,after:t}){let n=J(F),s=re(n.path),o=e.props.min_width??320,i=e.props.columns,l=i?`grid-template-columns: repeat(${i}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${o}px, 100%), 1fr))`,a=e.children??[],c=a.filter(d=>s.removed.includes(d.id)).map(d=>d.id),u=on(a.filter(d=>!c.includes(d.id)),s.order[e.id]),$=(d,m)=>{let f=u.map(b=>b.id).filter(b=>b!==d);if(f.splice(f.indexOf(m),0,d),sn(n.path,e.id,f),e.id===en){let b=h=>a.find(k=>k.id===h)?.data?.main?.params?.y?.[0],C=f.map(h=>n.pins.find(k=>k.y===b(h))).filter(h=>!!h);nn(n.path,[...C,...n.pins.filter(h=>!C.includes(h))])}};return r`<div class="grid" style=${l}>
    ${u.map(d=>r`<${mo} key=${d.id} node=${d} path=${n.path} span=${s.spans[d.id]??d.props.span??1}
      columns=${i} onDrop=${m=>m!==d.id&&$(m,d.id)} />`)}
    ${t??null}
    ${c.length?r`<div class="grid-note"><button type="button" class="link small" onClick=${()=>He(n.path,c)}>${c.length} hidden · show</button></div>`:null}
  </div>`}var Ft=[1,2,"full"];function mo(e){let[t,n]=y(!1),s=Ft[(Ft.indexOf(e.span)+1)%Ft.length],o=i=>i==="full"?"full width":`${i} column${i===1?"":"s"}`;return r`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${i=>{i.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${i=>{i.preventDefault(),n(!1),e.onDrop(i.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${i=>i.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${x} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${o(e.span)}; click for ${o(s)}`}
        aria-label=${`Width ${o(e.span)}`} onClick=${()=>rn(e.path,e.node.id,s)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${ue} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function jt({root:e}){let t=J(F),n=re(t.path),s=w({method:"keys",params:{from:t.path},scope:t.path}).data,o=e.props.template;if(!o||!1)return null;let i=new Set(n.removed),l=new Set([...t.charted].filter(([f])=>!i.has(f)).flatMap(([,f])=>f)),a=n.added.filter(f=>!l.has(f)).map(f=>({block:"line",id:`added-${f}`,props:{y:f},data:{main:{...o,params:{...o.params,y:[f]}}}})),c=new Set([...l,...a.filter(f=>!i.has(f.id)).map(f=>f.props.y)]),u=(s?.metrics?.rows??[]).map(f=>f[0]).filter(f=>!c.has(f));if(!s||!(u.length||a.length))return null;let $=f=>[...t.charted].find(([b,C])=>i.has(b)&&C.includes(f))?.[0]??a.find(b=>i.has(b.id)&&b.props.y===f)?.id,d=f=>{let b=$(f);b?He(t.path,[b]):tt(t.path,C=>({added:[...C.added,f]}))},m=u.length?r`<div class="add-chart">
        <span class="add-chart-label"><${x} name="plus" size=${16} /> Add a chart</span>
        <${lt} single options=${u} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
          onChange=${([f])=>d(f)} />
      </div>`:null;return r`<${B}><${Wt} node=${{block:"grid",id:"added",props:{},children:a}} after=${m} /><//>`}function er({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[s,o]=y(()=>t.find(a=>a.id===n())?.id??t[0]?.id),i=a=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(a)}`),o(a)},l=t.find(a=>a.id===s)??t[0];return Ue?r`<div class="stack">${t.map(a=>r`<${ue} key=${a.id} node=${a} />`)}</div>`:r`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(a=>r`<button type="button" role="tab" id=${`tab-${a.id}`} aria-selected=${a.id===l?.id}
          aria-controls=${`panel-${a.id}`} onClick=${()=>i(a.id)}>${a.props.title??a.id}</button>`)}
    </div>
    ${l?r`<div class="stack" role="tabpanel" id=${`panel-${l.id}`} aria-labelledby=${`tab-${l.id}`}>
          ${(l.children??[]).map(a=>r`<${ue} key=${a.id} node=${a} />`)}
        </div>`:null}
  </div>`}function tr({node:e}){let t=Y("main"),n=J(F),s=D(Ne),o=e.props,i=Nn(t.data,o.rows,o.columns,o.lower??{},o.expected??[]),l=U.value.page==="group"?U.value.run:null,a=o.baseline===null||o.baseline===void 0?null:i.find(u=>u.label===String(o.baseline)),c=u=>P(E(n.path,{run:u}),{replace:l!==null});return r`<${Q} title=${o.title} caption=${o.caption} numbered result=${t}>
    ${t.data?r`<div class="table-wrap"><table class="runs scorecard">
          <thead><tr class="small">
            <th data-tip=${o.rows}>${xe(o.rows)}</th>
            ${o.columns.map(u=>r`<th class="num" data-tip=${u}>${On(u,n.metrics)}</th>`)}
          </tr></thead>
          <tbody onPointerLeave=${()=>Ne.set(null)}>
            ${i.map(u=>{let $=`${u.runs.includes(l??"")?"selected":""}${u.runs.includes(s??"")?" hovered":""}${u.queued?" queued":""}`;return r`<tr key=${u.label} class=${$} data-tip=${u.runs.length?`${u.runs.length} run${u.runs.length>1?"s":""}`:void 0}
                  onClick=${u.runs.length?()=>c(u.runs[0]):void 0}
                  onPointerEnter=${()=>Ne.set(u.runs[0]??null)}>
                <td>${u.label}${u===a?r` <${Se} tip="the others are compared to this row">baseline<//>`:null}${u.queued?r` <${Se}>queued<//>`:null}</td>
                ${u.scores.map((d,m)=>$o(d,u.live,a?.scores[m]??null))}
              </tr>`})}
          </tbody>
        </table></div>`:r`<div class="skeleton late" style="block-size: 120px"></div>`}
  <//>`}function $o(e,t,n){if(!e)return r`<td class="num muted">–</td>`;let s=n&&n!==e?`${e.mean-n.mean>=0?"+":"\u2212"}${G(Math.abs(e.mean-n.mean))} against the baseline`:"",o=`${xt(e.mean)}${e.std===null?"":` \xB1 ${xt(e.std)}`}, ${e.n} run${e.n>1?"s":""}${s?`. ${s}`:""}`,i=`num score${e.best?" best":""}${t?" live":""}`;return r`<td class=${i} style=${e.shade===null?void 0:`--shade: ${e.shade}`} data-tip=${o}>
    ${G(e.mean)}${e.std===null?null:r`<span class="spread"> ± ${G(e.std)}</span>`}</td>`}var nr={section:Js,row:Qs,grid:Wt,line:An,table:Wn,scorecard:tr,importance:_s,stat:Fn,images:Ys,text:Zs,proposal:bs,note:Es,output:Cs,config:Rs,memory:vs,groups:ys,notes:ws,tabs:er,scatter:Hn,bar:Kn,histogram:Un,data_table:In,timeline:_n,custom:Is,markdown:Ss},fo=new Set(["line","scatter","bar","histogram"]);function ue({node:e}){return fo.has(e.block)?r`<${ho} node=${e} />`:r`<${Tt} node=${e} blocks=${nr} />`}function ho({node:e}){let t=J(F);return re(t.path).removed.includes(e.id)?r`<div class="grid-note"><button type="button" class="link small" onClick=${()=>He(t.path,[e.id])}>1 hidden · show</button></div>`:r`<${Tt} node=${e} blocks=${nr} />`}function sr(e,t){let n=e.split(`
`),s=t.split(`
`),o=n.length,i=s.length,l=Array.from({length:o+1},()=>new Uint32Array(i+1));for(let $=o-1;$>=0;$--)for(let d=i-1;d>=0;d--)l[$][d]=n[$]===s[d]?l[$+1][d+1]+1:Math.max(l[$+1][d],l[$][d+1]);let a=[],c=0,u=0;for(;c<o&&u<i;)n[c]===s[u]?(a.push({kind:"same",text:n[c]}),c++,u++):l[c+1][u]>=l[c][u+1]?a.push({kind:"removed",text:n[c++]}):a.push({kind:"added",text:s[u++]});for(;c<o;)a.push({kind:"removed",text:n[c++]});for(;u<i;)a.push({kind:"added",text:s[u++]});return a}function rr(e,t=3){let n=[],s=0;for(;s<e.length;){if(e[s].kind!=="same"){n.push(e[s++]);continue}let o=s;for(;o<e.length&&e[o].kind==="same";)o++;let i=s===0?0:t,l=o===e.length?0:t;o-s>i+l+1?n.push(...e.slice(s,s+i),{kind:"skip",count:o-s-i-l},...e.slice(o-l,o)):n.push(...e.slice(s,o)),s=o}return n}var Vt={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",config:"config",timeline:"timeline",proposal:"predictions"};function or(e){if(Vt[e.block])return Vt[e.block];if(e.block==="row"||e.block==="grid"){let n=new Set((e.children??[]).map(o=>Vt[o.block])),[s]=n;if(n.size===1&&s)return s}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function wt(e){let t=w(Xe(e.path)),n=me(),s=L(t.data),o=Te(()=>ot(s.map(m=>m["run.id"]),n),[t.data,n]),i=Te(()=>new Map(s.map(m=>[m["run.id"],m["run.name"]??m["run.id"]])),[t.data]),l=re(e.path),a=e.plain?"view plain":"sections view";if(!e.view)return r`<div class=${a}>${e.before}
      ${e.plain?r`<div class="skeleton late" style="block-size: 320px"></div>`:r`<${B} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let c=e.view.view,u={path:e.path,colors:o,names:i,metrics:e.view.metrics??{},charted:Gt(c),pins:l.main??e.view.pins??[]};if(e.plain)return r`<div class=${a}><${F.Provider} value=${u}><${ue} node=${c} /><//></div>`;let $=c.block==="section"&&!c.props.title?c.children??[]:[c],d=$.map(m=>Gt(m).size>0).lastIndexOf(!0);return r`<div class=${a}>${e.before}
    <${F.Provider} value=${u}>
      ${$.map((m,f)=>{let b=or(m);return r`<${Yt} key=${m.id}><${B} label=${b}><${at.Provider} value=${b}><${ue} node=${m} /><//><//>
          ${f===d?r`<${jt} root=${c} />`:null}<//>`})}
      ${d===-1?r`<${jt} root=${c} />`:null}
    <//>
  </div>`}function Gt(e,t=new Map){e.block==="line"&&t.set(e.id,e.data?.main?.params?.y??[]);for(let n of e.children??[])Gt(n,t);return t}function ar(e){if(null)return r`<div class="view-source small"><${x} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=D(U),s=n.page==="group"&&n.version,o=t.versions?r`<a href=${E(e.path,{history:!0})}><${x} name="history" size=${14} /> history (${t.versions})</a>`:null,i;switch(t.source){case"draft":i=r`draft <b>${t.draft}</b>`;break;case"view":i=r`${t.title?r`<em>${t.title}</em> · `:null}saved ${W(ke(t.version))} by ${t.author??"unknown"}`;break;default:i=r`the built-in view`}return r`<div class="view-source small">
    <${x} name="layout" size=${14} /><span>${i}</span>
    ${s?r`<a href=${E(e.path)}>an older version · show the current one</a>`:null}
    ${o}
    ${t.outdated?.length&&!s?r`<${go} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||s?null:r`<${bo} path=${e.path} />
        <${vo} path=${e.path} view=${t} />`}
  </div>`}function go(e){let[t,n]=y(null),s=e.outdated.map(i=>i.name).join(", ");return r`<button type="button" class="link small" onClick=${async()=>{n(null);try{await Jn(e.path)}catch(i){n(i.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${s} exists; update re-pins this view to it (a new version)`}>
      <${x} name="update" size=${14} /> update ${s}</button>
    ${t?r`<span class="bad-text small">${t}</span>`:null}`}function bo(e){let[t,n]=y(null);return r`<button type="button" class="link small" onClick=${async()=>{n(null);try{_e.set(await dt(e.path,null,""))}catch(o){n(o.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${x} name="file-text" size=${14} /> add text</button>
    ${t?r`<span class="bad-text small">${t}</span>`:null}`}function vo(e){let t=re(e.path),n=tn(t),[s,o]=y(!1),[i,l]=y(e.view.title??""),[a,c]=y(e.view.finding??""),[u,$]=y(null),[d,m]=y(!1);if(!n&&!s)return null;let f=async b=>{b.preventDefault(),m(!0),$(null);try{let C={charts:t.charts,view:t.view,added:t.added,removed:t.removed,order:t.order,spans:t.spans,main:t.main};await j("save_view",{path:e.path,prefs:C,title:i,finding:a}),tt(e.path,()=>({view:{},charts:{},added:[],removed:[],order:{},spans:{},main:null})),Le(h=>["view","view_history","summary"].includes(h.method)&&h.scope===e.path),o(!1)}catch(C){$(C.message)}finally{m(!1)}};return s?r`<form class="save-form" onSubmit=${f}>
    <${je} label="Title"><input value=${i} onInput=${b=>l(b.target.value)} /><//>
    <${je} label="Finding"><input value=${a} placeholder="the key result in one sentence"
        onInput=${b=>c(b.target.value)} /><//>
    <div class="save-actions">
      <${ee} type="submit" icon=${d?"hourglass":"save"} disabled=${d}>${d?"Saving\u2026":"Save as view"}<//>
      <${ee} icon="x" kind="quiet" onClick=${()=>o(!1)}>Cancel<//>
      ${u?r`<span class="bad-text small">${u}</span>`:null}
    </div>
  </form>`:r`<${ee} icon="save" class="save-view" onClick=${()=>o(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function ir(e){let t=w(ls(e.path)),n=t.data?.entries??[],[s,o]=y(null),i=s??n.slice(0,2).map(a=>a.version).reverse(),l=a=>{let c=i.includes(a)?i.filter(u=>u!==a):[...i,a].slice(-2);o(c.sort())};return t.status==="error"?r`<${R} kind="error">${t.error}<//>`:r`<section class="history">
    ${t.data&&!n.length?r`<${R}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((a,c)=>r`<li key=${a.version} class=${i.includes(a.version)?"picked":""}>
          <label><input type="checkbox" checked=${i.includes(a.version)} onChange=${()=>l(a.version)} />
            <span class="num muted" data-tip=${a.version}>${W(a.time)}</span>
            <b>${a.title??"untitled"}</b><span class="muted">${a.author??""}</span>
            ${a.message?r`<span>${a.message}</span>`:null}</label>
          <a href=${c===0?E(e.path):E(e.path,{version:a.version})}
            onClick=${u=>{u.preventDefault(),P(c===0?E(e.path):E(e.path,{version:a.version}))}}>${c===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${i.length===2?r`<${yo} path=${e.path} a=${i[0]} b=${i[1]} />`:null}
  </section>`}function yo(e){let t=a=>({method:"view_show",params:{group:e.path,version:a},scope:e.path}),n=w(t(e.a)).data,s=w(t(e.b)).data,o=w(ve(e.path,e.a)).data,i=w(ve(e.path,e.b)).data,l=n&&s?rr(sr(n.yaml,s.yaml)):[];return r`<div class="compare">
    <h3 class="block-title heading">Changes from ${W(ke(e.a))} to ${W(ke(e.b))}</h3>
    <pre class="diff code">${l.map(a=>a.kind==="skip"?r`<div class="diff-skip">⋯ ${a.count} unchanged lines</div>`:r`<div class=${`diff-${a.kind}`}>${a.kind==="added"?"+ ":a.kind==="removed"?"\u2212 ":"  "}${a.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${o?.title??e.a}</h3><${wt} path=${e.path} view=${o} plain /></div>
      <div><h3 class="block-title heading">${i?.title??e.b}</h3><${wt} path=${e.path} view=${i} plain /></div>
    </div>
  </div>`}function lr(e){return cs(e.path),e.history?r`<div class="page"><div class="sections">
      <${B} label=${cr(e.path)}><${zt} path=${e.path} /><//>
      <${B} label="history"><${ir} path=${e.path} /><//>
    </div></div>`:r`<div class="page">
    <${wo} path=${e.path} version=${e.version??null} draft=${e.draft??null} hiddenRuns=${e.hiddenRuns??!1} />
  </div>`}function wo(e){let t=re(e.path).main,n=yt(ve(e.path,e.version,e.draft,t),`${e.path}|${e.version}|${e.draft}`);T(()=>{n.status==="ready"&&requestAnimationFrame(mn)},[n.status==="ready"]),T(()=>{let o=i=>Ms(i.target.closest?.(".chart-frame")??null);return addEventListener("click",o,!0),()=>removeEventListener("click",o,!0)},[]);let s=r`
    <${B} label=${cr(e.path)}>
      <${zt} path=${e.path} finding=${n.data?.finding} />
      ${n.data?r`<${ar} path=${e.path} view=${n.data} />`:null}
    <//>
    ${ie(e.path.split("/").pop()??"")?null:r`${e.hiddenRuns?r`<${Ds} path=${e.path} />`:null}<${Ns} path=${e.path} />`}`;return n.status==="error"?r`<div class="sections">${s}
      <${B} label="view">
        ${ko(e.path,n.error)?r`<${R} kind="warning">${n.error} The page fills in once the remote answers again.<//>`:r`<${R} kind="error">${n.error}<//>`}
      <//>
    </div>`:r`<${wt} path=${e.path} view=${n.data} before=${s} />`}function cr(e){return ie(e.split("/").pop()??"")?"run":"group"}function ko(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function ur(e){T(()=>{Re(ve(e.id)).then(n=>P(E(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=w(ve(e.id));return t.status==="error"?r`<div class="page"><${R} kind="error">${t.error}<//></div>`:r`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var xo={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},qt=20,Be=-1,Co=[["day",86400],["week",7*86400],["month",30*86400]];function pr(e){let t=L(w($e()).data).map(a=>a.path),n=w({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),s=w({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});Ze("Timeline",L(n.data).filter(a=>a["run.status"]==="running").length);let o=Date.now()/1e3,i=L(n.data).filter(a=>a["run.created_at"]).map((a,c)=>({id:a["run.id"],name:a["run.name"]??a["run.id"],group:a["run.group"],status:a["run.status"],start:Date.parse(a["run.created_at"])/1e3,end:a["run.ended_at"]?Date.parse(a["run.ended_at"])/1e3:o,lane:c})),l=(s.data?.entries??[]).map(a=>({id:a.id,type:a.type,group:a.group,description:a.description,t:Date.parse(ke(a.id))/1e3}));return r`<div class="page timeline-page"><div class="sections">
    <${B} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${je} label="Group" inline>
          <select value=${e.from} onChange=${a=>P(nt(a.target.value),{replace:!0})}>
            ${t.map(a=>r`<option value=${a}>${a==="."?"everything":a}</option>`)}
          </select><//>
        <span class="muted small">${i.length} runs · ${l.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${B} label="runs">
      ${n.status==="error"?r`<${R} kind="error">${n.error}<//>`:null}
      ${n.data&&s.data?r`<${So} bars=${i} marks=${l} />`:r`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function So(e){let t=me(),n=N(null),s=[...e.bars.flatMap(h=>[h.start,h.end]),...e.marks.map(h=>h.t)],o=s.length?dr(Math.min(...s),Math.max(...s)):dr(Date.now()/1e3-86400,Date.now()/1e3),[i,l]=y(o),a=e.bars.length,c=Math.min(900,Math.max(160,(a+1.5)*qt+40)),$=zn(n,Bn,t?(h=>{let k=Pn(i[0],i[1]),p=v=>h.colors[xo[v]??"muted"],g=v=>h.colors[v==="verdict"?"good":v==="decision"?"accent":v==="question"?"warn":"muted"];return{style:bn(h),height:c,x:{range:i,log:!1,format:v=>Rn(v,k.step),label:"",splits:k.at},y:{range:[Be-.8,a+.5],log:!1,reverse:!0,label:"",size:150,splits:a<=40?[Be,...e.bars.map(v=>v.lane)]:[Be],format:v=>v===Be?"notes":No(e.bars[Math.round(v)]?.name??"")},draw:({ctx:v,x:A,y:H,px:V,focused:K})=>{let q=qt*.62*V;for(let O of e.bars){let M=A(O.start),S=Math.max(3*V,A(O.end)-M);v.fillStyle=K!==null&&K!==O.id?gn(p(O.status),.35):p(O.status),v.beginPath(),v.roundRect(M,H(O.lane)-q/2,S,q,3*V),v.fill()}for(let O of e.marks){let M=A(O.t),S=H(Be),se=(K===O.id?6:4.5)*V;v.fillStyle=g(O.type),v.beginPath(),v.moveTo(M,S-se),v.lineTo(M+se,S),v.lineTo(M,S+se),v.lineTo(M-se,S),v.closePath(),v.fill()}},hit:(v,A,H,V)=>{if(Math.abs(A-V(Be))<qt/2){let O=Do(e.marks,M=>Math.abs(H(M.t)-v),8);return O?{key:O.id,rows:To(O)}:null}let K=Math.round((A-V(0))/(V(1)-V(0))),q=e.bars.find(O=>O.lane===K&&H(O.start)-3<=v&&v<=Math.max(H(O.end),H(O.start)+3)+3);return q?{key:q.id,rows:Eo(q)}:null},onClick:v=>{let A=e.marks.find(H=>H.id===v);A?P(E(A.group,{drawer:!0})):P(oe(v))}}})(t):null,[i,e.bars,e.marks],t),d=h=>{if(!$.current)return;h.preventDefault();let k=$.current.xAt(h.clientX),p=Math.exp(h.deltaY*.0015);l(([g,v])=>Xt([k-(k-g)*p,k+(v-k)*p],o))},m=N(null),f=h=>m.current={x:h.clientX,range:i},b=h=>{if(!m.current||!$.current||!(h.buttons&1))return;let k=(h.clientX-m.current.x)*$.current.xPerPixel(),[p,g]=m.current.range;Math.abs(h.clientX-m.current.x)>3&&l(Xt([p-k,g-k],o))},C=Math.max(...s,Date.now()/1e3);return r`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${Co.map(([h,k])=>r`<button type="button" role="radio" aria-checked=${Math.abs(i[1]-i[0]-k)<1}
          onClick=${()=>l(Xt([C-k,C+k*.02],[Math.min(o[0],C-k),o[1]]))}>last ${h}</button>`)}
      <button type="button" role="radio" aria-checked=${i[0]===o[0]&&i[1]===o[1]} onClick=${()=>l(o)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${c}px`}
      onWheel=${d} onPointerDown=${f} onPointerMove=${b} onPointerUp=${()=>m.current=null}></div>
    <p class="muted small">${Mo(t)}</p>
  </div>`}function Eo(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:W(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:Me(e.end-e.start),color:null}]}function To(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:W(new Date(e.t*1e3).toISOString()),color:null}]}function Mo(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function Do(e,t,n){let s=null,o=n;for(let i of e){let l=t(i);l<o&&([s,o]=[i,l])}return s}function dr(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function Xt([e,t],n){let s=Math.min(n[1]-n[0],Math.max(60,t-e)),o=Math.max(n[0],Math.min(e,n[1]-s));return[o,o+s]}function No(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function mr(){let e=D(Ie),t=N(null);if(T(()=>{let o=t.current;if(!o||!e)return;o.showModal();let i=()=>Ie.set(null);return o.addEventListener("close",i),()=>o.removeEventListener("close",i)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},s=String(n.props.title??n.props.y??"Chart");return r`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${s} closedby="any">
    <${F.Provider} value=${e.view}><${ue} node=${n} /><//>
  </dialog>`}function $r(e,t){let n=e.toLowerCase(),s=t.toLowerCase();if(!n)return 1;let o=s.indexOf(n);if(o>=0)return 100-Math.min(o,50)-s.length/100;let i=0,l=0;for(let a of s)if(a===n[i]?i++:i>0&&l++,i===n.length)return 40-Math.min(l,39);return 0}function hr(e){let[t,n]=y(e.query),[s,o]=y(0),i=N(null),l=L(w($e()).data),a=L(w(mt()).data);T(()=>{let p=i.current;p.showModal();let g=()=>ne.set(null);p.addEventListener("close",g);let v=!1,A=K=>{let q=p.getBoundingClientRect();return K.clientX<q.left||K.clientX>q.right||K.clientY<q.top||K.clientY>q.bottom},H=K=>v=A(K),V=K=>v&&A(K)&&p.close();return"closedBy"in HTMLDialogElement.prototype||(p.addEventListener("pointerdown",H),p.addEventListener("pointerup",V)),()=>{p.removeEventListener("close",g),p.removeEventListener("pointerdown",H),p.removeEventListener("pointerup",V)}},[]);let c=()=>i.current?.close(),u=p=>()=>P(p),$=U.value,d=$.page==="group"?$.path:".",m=(p,g,v,A)=>({section:"Commands",label:p,detail:g,sym:{icon:v,tone:"muted",label:p},run:A}),b=[...l.map(p=>({section:"Groups",label:p.path==="."?"local":p.path,detail:`${p.runs} runs${p.proposal?` \xB7 ${p.proposal}`:""}`,sym:I("research",p.status),run:u(E(p.path))})),...a.map(p=>({section:"Runs",label:p["run.name"]??p["run.id"],detail:`${p["run.status"]} \xB7 ${p["run.path"]}`,sym:I("run",p["run.status"]),run:u(E(p["run.path"]))})),m("Theme: light","","sun",()=>rt("light")),m("Theme: dark","","moon",()=>rt("dark")),m("Theme: follow the system","","monitor",()=>rt("system")),m("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),m("Show notes and timeline","i","file-text",u(E(d,{drawer:!0}))),m("Show or hide the sidebar","\u2318B","panel-left",()=>te.set(!te.value)),m(ae.value?"Resume live updates":"Pause live updates","p",ae.value?"play":"pause",()=>ae.set(!ae.value)),m("Keyboard shortcuts","?","keyboard",()=>ye.set(!0)),m("Settings","","settings",u("/settings/appearance"))].map(p=>({it:p,s:Math.max($r(t,p.label),$r(t,p.detail)*.5)})).filter(p=>p.s>0).sort((p,g)=>g.s-p.s||fr(p.it.section)-fr(g.it.section)).slice(0,60).map(p=>p.it),C=p=>{p&&(c(),p.run())},h=p=>{if(p.key==="ArrowDown")o(Math.min(b.length-1,s+1));else if(p.key==="ArrowUp")o(Math.max(0,s-1));else if(p.key==="Enter")C(b[s]);else return;p.preventDefault()},k="";return r`<dialog class="sheet" ref=${i} aria-label="Search" closedby="any">
    <div class="palette-input"><${x} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${b[s]?`pal-${s}`:void 0}
        onInput=${p=>{n(p.target.value),o(0)}} onKeyDown=${h} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${b.map((p,g)=>{let v=p.section!==k&&!t?k=p.section:null;return r`${v?r`<li class="palette-head small" role="presentation">${v}</li>`:null}
          <li id=${`pal-${g}`} class="item" role="option" aria-selected=${g===s}
              onMouseMove=${()=>o(g)} onClick=${()=>C(p)}>
            <${z} spec=${p.sym} /><span class="label">${p.label}</span><span class="detail small">${p.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function fr(e){return["Groups","Runs","Commands"].indexOf(e)}function kt(e,t=[]){let n=new Map,s=(a,c={})=>({path:a,name:a==="."?"local":a.split("/").pop(),runs:c.runs??0,running:c.running??0,failed:(c.failed??0)+(c.killed??0)+(c.lost??0),status:c.status??null,children:[]});for(let a of e)n.set(a.path,s(a.path,a));(t.length===0||t.some(a=>a.name==="."))&&!n.has(".")&&n.set(".",s("."));for(let a of t){let c=a.name;n.has(c)||n.set(c,s(c)),Object.assign(n.get(c),{state:a.state,error:a.error})}for(let a of n.values()){if(X(a.path))continue;let c=a.path.lastIndexOf("/"),u=c<0?".":a.path.slice(0,c);(n.get(u)??n.get(De(a.path))??n.get(".")).children.push(a)}for(let a of n.values())a.children.sort((c,u)=>c.name.localeCompare(u.name));let i=[...n.values()].filter(a=>a.path!=="."&&X(a.path)).sort((a,c)=>a.name.localeCompare(c.name)),l=n.get(".");return l?[l,...i]:i}function gr(e,t,n,s=new Set){let o=[],i=n.toLowerCase(),l=a=>{(!i||a.path.toLowerCase().includes(i)||br(a,i))&&(o.push(a),(i||(X(a.path)?!s.has(a.path):t.has(a.path)))&&a.children.forEach(l))};return e.forEach(l),o}function br(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||br(n,t))}function vr(e,t){if(!t||X(t))return e;let n=t.split("/"),s=new Set(e);for(let o=t.startsWith("@")?2:1;o<n.length;o++)s.add(n.slice(0,o).join("/"));return s.size===e.size?e:s}function yr(e,t){if(X(t))return e;let n=t.lastIndexOf("/"),s=n<0?".":t.slice(0,n),o=i=>i.path===s?i:i.children.map(o).find(l=>l)??null;return e.map(o).find(i=>i)?.children??[]}function wr(e){return X(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function kr(){let e=D(U),t=w($e()),[n,s]=y(()=>new Set(Ce("open",[]))),[o,i]=y(()=>new Set(Ce("closed-hosts",[]))),[l,a]=y(""),c=N(null),u=e.page==="group"?e.path:null,$=kt(L(t.data),t.data?.meta?.sources??[]),d=gr($,n,l,o),m=h=>X(h)?!o.has(h):n.has(h),f=(h,k)=>{let p=k??!m(h);if(X(h)){let v=new Set(o);p?v.delete(h):v.add(h),he("closed-hosts",[...v]),i(v);return}let g=new Set(n);p?g.add(h):g.delete(h),he("open",[...g]),s(g)},b=N(u);return T(()=>{let h=vr(n,u);h!==n&&(he("open",[...h]),s(h)),u!==b.current&&u&&!X(u)&&o.has(De(u))&&f(De(u),!0),b.current=u},[u]),r`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${x} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${l} aria-label="Filter groups"
        onInput=${h=>a(h.target.value)} />
    </label>
    <div class="tree" ref=${c} onKeyDown=${h=>{let k=[...c.current?.querySelectorAll("a.tree-item")??[]],p=k.indexOf(document.activeElement),g=d[p];switch(h.key){case"ArrowDown":k[Math.min(k.length-1,p+1)]?.focus();break;case"ArrowUp":k[Math.max(0,p-1)]?.focus();break;case"ArrowRight":g?.children.length&&f(g.path,!0);break;case"ArrowLeft":g?.children.length&&m(g.path)?f(g.path,!1):g&&k[d.findIndex(v=>v.path===Ro(g.path))]?.focus();break;default:return}h.preventDefault()}} role="tree">
      ${d.map(h=>r`<${Po} key=${h.path} node=${h} current=${h.path===u}
        open=${m(h.path)||!!l} filtering=${!!l} onToggle=${()=>f(h.path)} />`)}
    </div>
  </nav>`}function Po(e){let t=e.node,n=()=>Ye(t.path),s=t.children.length>0,o=t.state==="unreachable";return r`<a class=${`tree-item${e.current?" current":""}${X(t.path)?" source-root":""}`} href=${E(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${s?e.open:void 0}
      style=${`padding-inline-start:${8+wr(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${i=>{i.metaKey||i.ctrlKey||(i.preventDefault(),e.current&&s&&!e.filtering?e.onToggle():P(E(t.path)))}}>
    <span class=${`twisty${s?" expandable":""}`} aria-disabled=${s&&e.filtering?"true":void 0}
      onClick=${i=>{s&&(i.preventDefault(),i.stopPropagation(),e.filtering||e.onToggle())}}>
      ${s?r`<${x} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    ${X(t.path)?r`<${z} size=${14} spec=${{icon:o?"cloud-off":"server",tone:"muted",label:o?`Unreachable: ${t.error??"no answer"}`:t.path==="."?"This machine":`Remote host ${t.name}`}} />`:null}
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?r`<${z} spec=${I("run","running")} size=${14} />`:null}
      ${t.failed?r`<${z} spec=${{...I("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function Ro(e){if(X(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function Cr(){let e=D(U),t=D(te),n=D(ne),s=D(ye),o=N(null);T(()=>pn(()=>o.current),[]),T(()=>(addEventListener("keydown",xr),()=>removeEventListener("keydown",xr)),[]);let i=e.page==="group"&&e.drawer,l;switch(e.page){case"group":l=r`<${lr} key=${`${e.path} ${e.version} ${e.draft} ${e.history} ${e.hiddenRuns}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} hiddenRuns=${e.hiddenRuns} />`;break;case"run":l=r`<${ur} id=${e.id} />`;break;case"settings":l=r`<${ms} />`;break;case"timeline":l=r`<${pr} key=${e.from} from=${e.from} />`;break;default:l=r`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return le||!1?r`<main class="main render-main" ref=${o}>${l}</main>`:r`<div class=${`shell${t?"":" no-sidebar"}${i?" with-drawer":""}`}>
    <${fs} />
    ${t?r`<${kr} />`:null}
    <main class="main" ref=${o}>${l}</main>
    ${i?r`<${Ts} path=${e.path} run=${e.run} />`:null}
    <${hs} />
    ${n!==null?r`<${hr} query=${n} />`:null}
    ${s?r`<${Io} />`:null}
    <${mr} />
  </div>`}function xr(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),ne.set(ne.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),te.set(!te.value);return}if(e.key==="Escape"){if(ne.value!==null||ye.value)return;let s=U.value;return s.page==="group"&&s.run?P(E(s.path,{drawer:!0}),{replace:!0}):s.page==="group"&&s.drawer?P(E(s.path),{replace:!0}):void 0}if(t||e.altKey||ds(e)||ne.value!==null||ye.value)return;let n=U.value;switch(e.key){case"/":e.preventDefault(),ne.set("");break;case"?":ye.set(!ye.value);break;case"p":ae.set(!ae.value);break;case"i":n.page==="group"&&P(E(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":te.set(!te.value);break;case"[":case"]":n.page==="group"&&Lo(n.path,e.key==="]"?1:-1);break}}async function Lo(e,t){let n=await Re($e()),s=yr(kt(L(n),n?.meta?.sources??[]),e),o=s.findIndex(l=>l.path===e),i=s[o+t];i&&P(E(i.path))}function Io(){let e=N(null);return T(()=>{let t=e.current;t.showModal();let n=()=>ye.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),r`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${$t.map(([t,n])=>r`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${ee} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}$n();if(le){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(ge.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Ke.n,fn&&kn()}jn();var _o=j("meta").then(e=>(le&&(e={...e,settings:{...e.settings,theme_mode:ge.value}}),ft(e),e));!le&&!!1&&dn(async()=>{let[e,t]=await Promise.all([_o,j("meta")]);e.bundle!==t.bundle?location.reload():ft(t)});Zt(r`<${Cr} />`,document.getElementById("app"));
