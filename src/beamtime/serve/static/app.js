import{$ as ot,$a as jn,A as pn,Aa as Sn,B as Re,Ba as qe,C as ie,Ca as ct,D as E,Da as Dt,E as nt,F as re,Fa as En,G as pe,H as Me,Ha as Pt,I as q,Ia as Tn,J as U,K as mn,La as Mn,M as R,Ma as Dn,N as $n,Na as Pn,O as fn,Oa as _n,P as le,Pa as In,Q as Ue,Qa as On,R as hn,Ra as zn,S as st,T as De,Ta as Bn,U as ge,V as yn,Va as An,W as Tt,Wa as Hn,X as rt,Xa as Kn,Y as F,Ya as Un,Z as J,Za as Fn,_ as me,_a as Wn,a as r,aa as wn,b as tn,c as Ae,ca as Le,d as se,da as be,e as tt,fa as kn,ga as xn,h as nn,ha as x,i as sn,ia as O,j as He,ja as at,k as rn,ka as oe,l as on,la as z,m as an,ma as L,na as We,oa as I,pa as Ce,q as j,qa as B,r as Ke,ra as Q,s as Ne,sa as je,t as Et,ta as Ve,u as k,ua as it,v as ln,va as lt,w as ae,wa as _,x as cn,xa as Ge,y as un,ya as Mt,z as dn,za as Cn}from"./chunks/chunk-QXSDQEZJ.js";import{a as en,b as Qe}from"./chunks/chunk-O2K4N3UR.js";import{$ as Ln,C as fe,D as M,E as xe,F as he,K as gn,M as Fe,Q as bn,R as vn,V as Nn,_ as Rn,b as Zt,d as Jt,f as y,g as T,h as Qt,i as N,j as Ee,k as Z,q as G,r as St,t as ke,u as de,v as Te,w as et,x as W,y as Be}from"./chunks/chunk-A2X3XNU4.js";import"./chunks/chunk-VC46IEJQ.js";function Pe(e,t){Re(n=>t.includes(n.method)&&n.scope!==null&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var Nt=["notes","timeline","groups","check","card","memory_show","status"];async function ut(e,t){let n=e.meta??{};await j("note_add",{group:e.group,type:t.type??e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),Pe(e.group,Nt)}async function Vn(e,t,n,s){await j("note_add",{group:e,type:t,description:n,body:s}),Pe(e,Nt)}async function Gn(e,t){await j("memory_update",{group:e,body:t}),Pe(e,["memory_show","status"])}async function qn(e,t){let n=await j("proposal_show",{group:e}),s=Object.fromEntries(Object.entries(n.proposal??{}).filter(([o])=>!["schema","author","user","supersedes"].includes(o)));await j("proposal_set",{group:e,proposal:{...s,statement:t}}),Pe(e,["groups","proposal_show","check","summary"])}async function Xn(e){await j("note_rm",{note:e.id}),Pe(e.group,Nt)}async function Yn(e,t,n){await j("name",{run:e,name:n}),Pe(t,["card","runs","groups","summary","series"])}async function Rt(e,t){await j("run_promote",{runs:[pe(e,t)]}),Pe(t,["card","runs","groups","summary","series","keys","check","proposal_show","status"])}async function dt(e,t,n){let s=await j("view_text",{path:e,id:t,text:n});return Re(o=>["view","view_history"].includes(o.method)&&o.scope===e),s.id}async function Zn(e){await j("view_upgrade",{group:e}),Re(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var _e=new fe(null);async function Jn(e,t){return await j("set",{key:e,value:t}),j("meta")}var $e=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),ve=(e,t=null,n=null,s=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{},...s?{metrics:s}:{}},scope:e}),Lt=(e,t=null)=>({method:"summary",params:{path:e,...t?{metrics:t}:{}},scope:e}),Ie=e=>({method:"groups",params:{from:e,depth:0},scope:e}),Qn=e=>({method:"check",params:{group:e},scope:e}),es=e=>({method:"proposal_show",params:{group:e},scope:e}),Oe=(e,t)=>({method:"card",params:{run:pe(e,t)},scope:t}),ts=(e,t)=>({method:"output",params:{run:pe(e,t),tail:30},scope:t}),ns=(e,t)=>({method:"run_diff",params:{run:pe(e,t)},scope:t}),Xe=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),ss=e=>({method:"runs",params:{from:e,hidden:!0,where:{"run.hidden":!0},select:["run.name","run.status","run.created_at"],limit:200},scope:e}),pt=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),rs=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),os=()=>({method:"status",params:{},scope:"."}),mt=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function Ye(e){let t=Ae(e).value.main;for(let n of[ve(e,null,null,t),Ie(e),Xe(e),Lt(e,t)])Et(n);Ne(ve(e,null,null,t)).then(n=>{for(let s of as(n.view))Et(s)}).catch(()=>{})}function as(e){return e?[...xr.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(as)]:[]}var xr=new Set(["line","custom"]),is=e=>({method:"view_history",params:{group:e},scope:e});var ft="/static/favicon.svg",$t=null;async function Cr(){if($t)return $t;let e=new Image;e.src=ft,await e.decode();let t=32,n=document.createElement("canvas");n.width=n.height=t;let s=n.getContext("2d");if(!s)return ft;let o=getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();return o?(s.drawImage(e,0,0,t,t),s.beginPath(),s.arc(t-6,t-6,6,0,Math.PI*2),s.fillStyle=o,s.fill(),$t=n.toDataURL("image/png"),$t):ft}function Sr(e){if(!1)return;let t=document.querySelector("link[rel=icon]");if(t instanceof HTMLLinkElement){if(!e){t.type="image/svg+xml",t.href=ft;return}Cr().then(n=>{t.type="image/png",t.href=n})}}function Ze(e,t=0){T(()=>{document.title=`${t?`(${t}) `:""}${e} \xB7 Beamtime`,Sr(t>0)},[e,t])}function ls(e){let t=ie(e.split("/").pop()??""),n=k(t?null:Ie(e)),s=k(t?Oe(e.split("/").pop()??"",e):null),o=t?s.data?.run.name??s.data?.run.id??e:e==="."?"local":e.split("/").pop()??e,i=t?s.data?.run.status==="running"?1:0:L(n.data)[0]?.running??0;Ze(o,i)}var ee=new fe(xe("sidebar",!0)),te=new fe(null),ye=new fe(!1),we=new fe(null);ee.subscribe(e=>he("sidebar",e));var cs=xe("visit",Date.now());he("visit",Date.now());function us(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var ht=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var Er=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function gt(e){we.set(e),dn(e.stale),st.set(e.theme),Fe.set(e.colormaps),e.settings?.theme_mode&&ge.set(e.settings.theme_mode),Tt()}var ds=0;async function _t(e,t){let n=++ds;e==="theme_mode"&&(ge.set(t),Tt());let s=await Jn(e,t);n===ds&&gt(s)}function ps(){let e=M(ge),t=me(),n=M(we),[s,o]=y(null);Ze("Settings");let i=(l,u)=>{o(null),_t(l,u).catch($=>o($.message))},c=n?.settings??{},a=(l,u,$)=>r`
    <label class="field-label small" for=${`setting-${l}`}>${u}</label>
    <span class="input body">
      <select id=${`setting-${l}`} value=${c[l]} onChange=${d=>i(l,d.target.value)}>
        ${$.map(d=>r`<option value=${d}>${d}</option>`)}
      </select>
    </span>`;return r`<div class="page settings"><div class="sections">
    <${B} label="settings">
      <h1 class="page-title title" tabindex="-1">Settings</h1>
      <p class="muted small">Changes are written to <code>${c.file??"beamtime.yaml"}</code>, the project's settings.</p>
      ${s?r`<${z} kind="error">${s}<//>`:null}
    <//>
    <${B} label="appearance">
      <div class="settings-rows">
        <span class="field-label small">Mode</span>
        <div class="segmented" role="radiogroup" aria-label="Theme mode">
          ${Er.map(([l,u,$])=>r`<button type="button" role="radio" aria-checked=${e===l} onClick=${()=>i("theme_mode",l)}>
            <${x} name=${u} size=${15} />${$}</button>`)}
        </div>
        ${a("theme","Theme",n?.themes??[])}
      </div>
      <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files recolor this layout: they go in <code>themes/</code> next to
        beamtime.yaml. Colormaps are chosen in each chart's settings.</p>
      ${(n?.theme?.problems??[]).map(l=>r`<${z} kind="warning">${l}<//>`)}
    <//>
    <${B} label="figures">
      <div class="settings-rows">
        <span class="field-label small">Style sheets</span>
        ${(n?.figure_styles??[]).length?r`<${lt} options=${n.figure_styles} value=${c.figure_style??[]} label="Style sheets"
              placeholder="Add a style" onChange=${l=>i("figure_style",l)} />`:r`<span class="muted small"><code>${JSON.stringify(c.figure_style??[])}</code>; choosing others needs the figures
              extra: <code>uv add matplotlib scienceplots</code></span>`}
      </div>
      <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(c.figure_style??[])})</code>, in this order
        (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
        <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <//>
    <${B} label="keyboard">
      <table class="kv">${ht.map(([l,u])=>r`<tr><td><kbd class="small">${l}</kbd></td><td>${u}</td></tr>`)}</table>
    <//>
    <${B} label="about">
      <table class="kv">
        <tr><td class="muted">version</td><td>${n?.version}</td></tr>
        <tr><td class="muted">root</td><td><code class="code">${n?.root}</code></td></tr>
        ${(n?.sources??[]).map(l=>r`
          <tr><td class="muted">${l.name==="."?"local":l.name}</td><td><code class="code">${l.logdir}</code> (${l.kind}, ${l.state})</td></tr>`)}
      </table>
    <//>
  </div></div>`}var ms={system:"light",light:"dark",dark:"system"},Tr={system:"monitor",light:"sun",dark:"moon"};function $s(){let e=M(we),t=M(ge),n=M(ee);return r`<header class="topbar">
    <${I} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>ee.set(!n)} />
    <a class="project heading" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>te.set("")} aria-label="Search (⌘K)">
      <${x} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${Mr} />
      <${I} icon=${Tr[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${ms[t]})`}
        onClick=${()=>{_t("theme_mode",ms[t])}} />
      <a class="icon-button" href=${nt(U.value.page==="group"?U.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${x} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${x} name="settings" size=${16} /></a>
    </div>
  </header>`}function Mr(){let t=(k($e()).data?.meta?.sources??[]).filter(n=>n.name!==".");return t.length?r`${[{name:".",state:"connected"},...t].map(n=>r`<a class=${`source small ${n.state}`}
      href=${E(n.name)}
      data-tip=${n.state==="connected"?`${n.name==="."?"local":n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${x} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name==="."?"local":n.name}</a>`)}`:r`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${x} name="server" size=${15} /> local</span>`}function Dr(e){let[t,n]=y(Date.now());return T(()=>{let s=setInterval(()=>n(Date.now()),e);return()=>clearInterval(s)},[e]),t}function Pr(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function fs(){let e=M(cn),t=M(ae),n=M(un),s=M(U),o=Dr(5e3),i=k(os()).data,c=L(k(mt()).data),a=M(we),l=i?.daemon,u=i?.runs?.running??0,$=c.filter(C=>C["run.status"]==="failed"&&Pr(C["run.ended_at"])>cs).length,d=i?.meta?.freshness,[m,f,g]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&l?["",`live \xB7 updated ${W(new Date(n).toISOString(),o)}`,`beamtime serve, pid ${l.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return r`<footer class="statusbar small">
    <span class="status-item" data-tip=${g}><span class=${`live-dot ${m}`}></span>${f}</span>
    ${u?r`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>te.set("running")}>
          <${x} name="circle-dot" size=${14} class="tone-accent" />${u} running</button>`:null}
    ${$?r`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>te.set("failed")}>
          <${x} name="circle-x" size=${14} />${$} failed since your last visit</button>`:null}
    ${d?.behind?r`<span class="status-item warn-text" data-tip=${d.text}><${x} name="hourglass" size=${14} />${d.behind} runs behind</span>`:null}
    ${d?.damaged?.length?r`<span class="status-item warn-text" data-tip=${d.damaged.join(`
`)}><${x} name="triangle-alert" size=${14} />${d.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${s.page==="group"&&s.run?r`<span class="status-item"><${x} name="activity" size=${14} />1 run selected</span>`:null}
    <${I} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>ae.set(!t)} />
    ${a?.outdated?r`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item">${a?.version?`beamtime ${a.version}`:""}</span>
  </footer>`}var hs=null;function bt(e){let t=N(null),[n,s]=y(null),[o,i]=y(!1),[c,a]=y(!1);T(()=>{let d=!0;return hs??=import("./chunks/md-SW3VT2BQ.js"),hs.then(m=>m.render(e.text??"")).then(m=>d&&s(m)),()=>{d=!1}},[e.text]),Qt(()=>{let d=t.current;if(!d||!e.clamp)return;let m=()=>a(d.scrollHeight>d.clientHeight+2),f=new ResizeObserver(m);return f.observe(d),()=>f.disconnect()},[e.clamp,n]);let l=e.clamp&&!o,u=`md${l?" clamped":""}`,$=l?`--clamp:${e.clamp}`:"";return r`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?r`<div class=${u} ref=${t} style=${$}>
          ${(e.text??"").split(/\n{2,}/).map(d=>r`<p>${d}</p>`)}
        </div>`:r`<div class=${u} ref=${t} style=${$} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(c||o)?r`<button type="button" class="link small more" onClick=${()=>i(!o)}>${o?"less":"more"}</button>`:null}
  </div>`}function Se(e){let[t,n]=y(!!e.startEditing),[s,o]=y(e.value),[i,c]=y(null),[a,l]=y(null),u=N(null),$=N(!1);T(()=>c(null),[e.value]),T(()=>{!t||!u.current||(u.current.focus(),e.startEditing?u.current.select():u.current.setSelectionRange(u.current.value.length,u.current.value.length))},[t]);let[d,m]=y(!1),f=e.locked??void 0,g=b=>{if(!b.target.closest("a, button, input, summary")){if(f)return m(!0);b.preventDefault(),o(i??e.value),l(null),$.current=!1,n(!0)}},C=()=>{$.current=!0,n(!1),l(null),e.onCancel?.()},h=async()=>{if($.current)return;$.current=!0;let b=e.multiline?s.trim():s.replace(/\s*\n\s*/g," ").trim();if(b===e.value.trim()||!b&&!e.multiline)return C();n(!1),c(b);try{await e.onSave(b)}catch(v){c(null),o(b),l(v.message),$.current=!1,n(!0)}},w=b=>{if(b.key==="Escape")return b.preventDefault(),b.stopPropagation(),C();b.key!=="Enter"||b.isComposing||b.keyCode===229||(!e.multiline||b.metaKey||b.ctrlKey)&&(b.preventDefault(),h())};if(t)return r`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${u} class="edit-field" value=${s} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,s.split(`
`).length+1)):1}
        onInput=${b=>o(b.target.value)} onKeyDown=${w} onBlur=${h}></textarea>
      <span class="edit-hint small">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${a?r` · <span class="bad-text">${a}</span>`:null}</span>
    </div>`;let p=i??e.value;return r`<div class=${`editable${f?" locked":""}${i!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${f?`${e.label}: ${f}`:`Edit ${e.label}`}
      data-tip=${f} onClick=${g} onBlur=${()=>m(!1)}
      onKeyDown=${b=>b.key==="Enter"&&b.target===b.currentTarget&&g(b)}>
    ${p.trim()?e.render?e.render(p):p:r`<span class="muted">${e.placeholder??"Click to write"}</span>`}
    ${d&&f?r`<span class="edit-hint small locked-why" role="status"><${x} name="lock" size=${14} /> ${f}</span>`:null}
  </div>`}function It(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function gs({node:e}){let t=J("proposal"),n=J("check"),s=t.data,o=n.data;if(!s)return r`<${oe} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let i=s.proposal??{},c=(s.versions??[]).filter(l=>l.version!==s.version),a=!e.props.of||e.props.of===".";return r`<${oe} title="Predictions" result=${t} class="proposal">
    ${a?null:r`<p class="statement">${i.statement}</p>`}
    ${i.rationale?r`<p class="rationale prose">${i.rationale}</p>`:null}
    <${Sn} predictions=${o?.predictions} />
    ${c.length?r`<${Ve} summary=${`${c.length} earlier version${c.length>1?"s":""}`}>
          ${c.map(l=>r`<p class="small"><code>${l.version}</code> ${l.statement}
            <span class="muted">(${l.runs} runs, check ${l.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function bs({node:e}){let t=J("main"),n=e.data?.main.params.group??".",s=t.data?.chain??[],o=s.find(a=>a.group===n)??null,i=s.filter(a=>a.group!==n),c=o?.notes_since?"out of date":o?`version ${o.versions??1}`:"none yet";return r`<${We} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?c:void 0} open=${!1} result=${t}
      action=${r`<${O} spec=${{icon:"circle-help",tone:"muted",label:Rr}} />`}>
    <${Se} value=${o?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${a=>r`<${bt} text=${a} />`} onSave=${a=>Gn(n,a)} />
    ${o&&(o.body?.length>(t.data?.budget??1/0)||o.notes_since>=Nr)?r`<p class="memory-meta small warn-text">${o.body?.length>t.data.budget?`${o.body.length} characters, beyond the budget of ${t.data.budget}`:`${o.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${o?r`<p class="memory-meta small">${o.author} · covers notes until ${o.covers_until?.slice(0,10)}
          ${o.notes_since?r` · <span class="warn-text">${o.notes_since} newer note${o.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${i.length?r`<p class="memory-meta small">Memory above this group: ${i.map((a,l)=>r`${l?", ":""}<a href=${E(a.group)}>${a.group==="."?"local":a.group}</a>`)}</p>`:null}
  <//>`}var Nr=5,Rr="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",Lr="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function vs({node:e}){let t=J("main"),n=e.data?.main.params.from??".",s=L(t.data).filter(o=>o.path!==n);return r`<${oe} title=${e.props.title} count=${t.data?String(s.length):void 0} result=${t}>
    ${t.data&&!s.length?r`<${z}>No groups below.<//>`:null}
    <div class="group-list">
      ${s.map(o=>{let[i,c]=It(o.progress),a=(o.failed??0)+(o.killed??0)+(o.lost??0);return r`<a class="group-row" key=${o.path} href=${E(o.path)}
            onPointerEnter=${()=>Ye(o.path)} onFocus=${()=>Ye(o.path)}>
          <${O} spec=${_("research",o.status)} />
          <span class="gname heading">${o.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${o.status!=="concluded"?r`<span class=${`tone-${_("research",o.status).tone}`}>${_("research",o.status).label}</span>`:null}
            ${o.check?r`<${O} spec=${_("result",o.check)} word />`:null}
            ${o.verdict?r`<${O} spec=${_("verdict",o.verdict)} />`:null}
            ${i?r`<span data-tip=${c}>${i}</span>`:null}
            <span class="num"><b>${o.runs}</b> runs</span>
            ${o.running?r`<${O} spec=${_("run","running")} />`:null}
            ${a?r`<span class="tone-bad num" data-tip="failed, killed or lost"><${x} name="circle-x" size=${14} /> ${a}</span>`:null}
          </span>
          ${o.proposal?r`<span class="gstatement caption">${o.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function ys({node:e}){let t=J("main"),n=e.data?.main.params.from??".",[s,o]=y(!1),i=(t.data?.entries??[]).filter(a=>!String(a.state??"").startsWith("superseded")),c=t.data?.meta?.matched??i.length;return r`<${We} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(c):void 0} result=${t}
      action=${r`<${O} spec=${{icon:"circle-help",tone:"muted",label:Lr}} />
        ${r`<${I} icon="plus" label="Add a note" onClick=${()=>o(!0)} />`}`}>
    <div class="notes">
      ${s?r`<${Or} group=${n} onDone=${()=>o(!1)} />`:null}
      ${t.data&&!i.length&&!s?r`<p class="muted small">No notes yet.</p>`:null}
      ${i.map(a=>r`<${vt} key=${a.id} note=${a} scope=${n} />`)}
      ${t.data?.more&&e.data?r`<${ws} call=${e.data.main} before=${i[i.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var _r=20;function ws(e){let[t,n]=y(!1),s=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:_r}}:null,o=k(s);if(!t)return r`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(o.status==="error")return r`<p class="bad-text small">${o.error}</p>`;let i=o.data?.entries??[];return r`${o.data?null:r`<div class="skeleton" style="block-size: 40px"></div>`}
    ${i.map(c=>r`<${vt} key=${c.id} note=${c} scope=${e.scope} />`)}
    ${o.data?.more?r`<${ws} call=${e.call} before=${i[i.length-1]?.id} scope=${e.scope} />`:null}`}var Ir=["observation","decision","idea","question","theory"];function ks(e){return(e?.note_types??Ir).filter(t=>t!=="verdict")}function Or(e){let t=ks(M(we)),[n,s]=y("observation"),[o,i]=y(""),[c,a]=y(""),[l,u]=y(null),[$,d]=y(!1),m=async g=>{if(g.preventDefault(),!o.trim())return u("give the note a title");d(!0);try{await Vn(e.group,n,o.trim(),c.trim()),e.onDone()}catch(C){u(C.message),d(!1)}};return r`<form class="note new-note" onSubmit=${m} onKeyDown=${g=>{g.key==="Escape"&&e.onDone(),g.key==="Enter"&&(g.metaKey||g.ctrlKey)&&m(g)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${n} aria-label="Note type" onChange=${g=>s(g.target.value)}>
        ${t.map(g=>r`<option value=${g}>${g}</option>`)}
      </select></span>
      <span class="input body new-note-field"><input class="new-note-title" value=${o} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${g=>i(g.target.value)} /></span>
    </div>
    <span class="input small"><textarea class="new-note-body" rows="4" value=${c} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${g=>a(g.target.value)}></textarea></span>
    <div class="save-actions">
      <${Q} type="submit" icon=${$?"hourglass":"plus"} disabled=${$}>${$?"Adding\u2026":"Add note"}<//>
      <${Q} icon="x" kind="quiet" onClick=${e.onDone}>Cancel<//>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${l?r`<span class="bad-text small">${l}</span>`:null}
    </div>
  </form>`}function zr({note:e}){let t=ks(M(we)).filter(n=>n!==e.type);return e.type==="verdict"?r`<span class="sym tone-accent" data-tip="a verdict's type can't change; write a new note">
      <${x} name=${_("note","verdict").icon} size=${15} /></span>`:r`<${it} icon=${_("note",e.type).icon} label="Change the note's type" title="Note type">
    <div class="menu-list">
      ${t.map(n=>r`<button type="button" key=${n} onClick=${()=>ut(e,{type:n})}>
        <${x} name=${_("note",n).icon} size=${15} /> ${n}</button>`)}
    </div>
  <//>`}function vt(e){let t=e.note,[n,s]=y(!!e.open),[o,i]=y(!1),c=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,a=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),l=t.meta?.author;return r`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${u=>!u.target.closest(".editable, a, .note-delete, .popover-wrap")&&s(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${x} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${zr} note=${t} />
      <${Se} value=${t.description} label="the note's title" class="note-title prose" render=${Ar}
        onSave=${u=>ut(t,{description:u})} />
      ${t.overall?r`<${O} spec=${_("verdict",t.overall)} />`:null}
      ${t.state?r`<${Ce} tone="warn">${t.state}<//>`:null}
      ${c?r`<a class="note-group small" href=${E(c)} data-tip="from this group">${Br(c,e.scope)}</a>`:null}
      <span class="note-meta small">${l?`${l} \xB7 `:""}${W(a)}</span>
      ${r`<${I} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${o}
        onClick=${u=>{u.stopPropagation(),i(!o)}} />`}
    </div>
    ${o?r`<div class="note-confirm small" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <${Q} icon="trash" kind="danger" onClick=${()=>{Xn(t)}}>Delete<//>
          <${Q} icon="x" kind="quiet" onClick=${()=>i(!1)}>Cancel<//>
        </div>`:null}
    ${n?r`<${Se} value=${t.body??""} label="the note" multiline class="note-body prose markdown"
          placeholder="Add details in Markdown" render=${u=>r`<${bt} text=${u} />`}
          onSave=${u=>ut(t,{body:u})} />`:null}
  </article>`}function Br(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,s=n.split("/").pop()??n;return ie(s)?s.slice(-8):n}function xs({node:e}){let t=J("main"),n=t.data?.lines??[],s=t.data?.meta??{},o=r`<${x} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${s.total_lines??n.length} lines${(s.shown??0)<(s.total_lines??0)?`, last ${s.shown}`:""}`:""}</span>`;return r`<${oe} result=${t}>
    <${Ve} summary=${o} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function Cs({node:e}){let t=Z(F);return r`<${oe} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${Se} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${_e.value===e.id} onCancel=${()=>_e.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>r`<${bt} text=${n} />`}
      onSave=${n=>(_e.set(null),dt(t.path,e.id,n))} />
  <//>`}function Ss({node:e}){return r`<${z} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function Ar(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let s=n.slice(2,-2),[o]=s.split(/[#@]/),i=o.split("/").pop()??"";return r`<a href=${ie(i)?re(i):E(o)}>${s}</a>`}return n.startsWith("`")?r`<code>${n.slice(1,-1)}</code>`:n})}function Hr(e,t){let n=/^(?:ssh|https?|git):\/\/(?:[^@/]*@)?([^/:]+)(?::\d+)?\/(.+?)(?:\.git)?\/?$/.exec(e??""),s=/^(?:[^@/]+@)?([^/:]+):(?!\/)(.+?)(?:\.git)?\/?$/.exec(e??""),[,o,i]=n??s??[];return!o||!i?null:o==="github.com"?{host:"GitHub",url:`https://github.com/${i}/commit/${t}`}:o==="gitlab.com"||o.startsWith("gitlab.")?{host:"GitLab",url:`https://${o}/${i}/-/commit/${t}`}:null}function yt(e){let{git:t,copied_from:n}=e.run,s=[];return t?.commit&&s.push(["code",r`<${Kr} git=${t} />`]),n&&s.push(["copied from",r`<a href=${re(n.id)} data-tip=${`${n.id}, ${n.at}`}>${n.path??n.id}</a>`]),e.checkpoints?.length&&s.push(["checkpoints",r`${e.checkpoints.map(o=>r`<${Ur} key=${o.name} ck=${o} />`)}`]),s}function Kr({git:e}){let t=Hr(e.remote,e.commit);return r`<span>${e.commit.slice(0,10)}${e.branch?r` on ${e.branch}`:null}
    ${e.dirty?r` <${Ce} tone="warn" tip="Uncommitted changes when the run started">dirty<//>`:null}
    ${t?r` · <a href=${t.url} target="_blank" rel="noopener noreferrer">${t.host}</a>`:null}</span>`}function Ur({ck:e}){let t=()=>{navigator.clipboard?.writeText(e.location)};return r`<div class="checkpoint">
    <span class=${e.exists?"":"muted"} data-tip=${e.location??void 0}>${e.name}</span>
    ${e.exists?null:r`<${Ce} tone="warn" tip=${e.location??void 0}>missing<//> <span class="muted">${Fr(e)}</span>`}
    ${e.location?r`<${I} icon="copy" label=${`Copy the path of ${e.name}`} onClick=${t} />`:null}
  </div>`}function Fr(e){return e.location?e.via==="origin"?"not found where the source run kept it":"not found at its recorded location":"no location recorded"}function wt({run:e,scope:t}){let[n,s]=y(!1),o=k(n?ns(e,t):null);return r`<${Ve} summary="Uncommitted changes" onToggle=${s}>
    ${o.error?r`<p class="muted small">${o.error}</p>`:null}
    ${o.data?r`<pre class="log code diff">${String(o.data.text).split(`
`).map(i=>r`<span class=${Wr(i)}>${i}\n</span>`)}</pre>`:n&&!o.error?r`<div class="skeleton late" style="block-size: 80px"></div>`:null}
  <//>`}function Wr(e){return e.startsWith("+++")||e.startsWith("---")||e.startsWith("@@")?"muted":e.startsWith("+")?"tone-good":e.startsWith("-")?"tone-bad":""}function Es(e){let t=()=>R(E(e.path),{replace:!0});return r`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${x} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${I} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?r`<${jr} id=${e.run} scope=${e.path} />`:r`<${Vr} path=${e.path} />`}
  </aside>`}function jr({id:e,scope:t}){let n=k(Oe(e,t)).data,s=k(ts(e,t)).data,o=k(Xe(t)).data,i=k({method:"keys",params:{from:t},scope:t}).data,c=me(),a=Ee(()=>ot(L(o).map(m=>m["run.id"]),c).get(e),[o,c,e]);if(!n)return r`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let l=n.run,u=Object.entries(n.metrics??{}),$=gn(a,c),d=yt(n);return r`<div class="drawer-body">
    <h3 class="heading"><span class=${$.class} style=${$.style}></span>
      <a href=${re(e)}>${l.name}</a></h3>
    <p class="facts small">
      <${O} spec=${Ge(l.status,l.exit)} word tip=${et(l)} />
      <span><b>${de(l.steps)}</b> steps</span>
      <span><b>${Te(l.duration_s)}</b></span>
      <span data-tip=${l.created_at}>${W(l.created_at)}</span>
    </p>
    ${l.error?r`<pre class="log code bad-text">${l.error}</pre>`:null}
    ${d.length?r`<table class="kv small">${d.map(([m,f])=>r`<tr><td class="muted">${m}</td><td>${f}</td></tr>`)}</table>`:null}
    ${l.git?.dirty?r`<${wt} run=${l.id} scope=${t} />`:null}
    <h4 class="small">Config</h4>
    <${ct} config=${n.config??{}} varying=${qe(i)} />
    ${u.length?r`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${u.map(([m,f])=>r`<tr><td>${m}</td><td class="num"><b>${G(f.last)}</b></td>
              <td class="num">${G(f.min)}</td><td class="num">${G(f.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?r`<h4 class="small">Cited by</h4>${n.cited_by.map(m=>r`<p class="small"><${O} spec=${_("note",m.type)} /> ${m.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(m=>r`<div class="event small"><span class="muted num">${m.t?.slice(5,16).replace("T"," ")}</span>
        <${x} name=${Mt(m.type)} size=${14} /><span>${m.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(s?.lines??[]).join(`
`)}</pre>
  </div>`}function Vr({path:e}){let t=k(pt(e)).data,n=k(rs(e)).data;return r`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?r`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(s=>!String(s.state??"").startsWith("superseded")).map(s=>r`<${vt} key=${s.id} note=${s} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(s=>r`<div class="event small"><span class="muted num">${s.t?.slice(5,16).replace("T"," ")}</span>
        <${x} name=${s.kind==="note"?"file-text":Mt(s.type)} size=${14} />
        <span>${s.run?r`<a href=${re(s.run)}>${s.run.slice(-8)}</a> `:null}${s.description??s.type}</span></div>`)}
  </div>`}function kt(e,t){let n=k(e),s=N(null);return n.status!=="loading"&&(s.current={scope:t,result:n}),n.status==="loading"&&s.current?.scope===t?s.current.result:n}var Ot=null;function Ts(e){Ot?.();let t=document.querySelector(".main");if(!e||!t)return;let n=e.getBoundingClientRect().top,s=new ResizeObserver(()=>{e.isConnected&&(t.scrollTop+=e.getBoundingClientRect().top-n)});for(let a of t.children)s.observe(a);let o=["wheel","touchmove","keydown","pointerdown"],i=()=>{s.disconnect(),clearTimeout(c);for(let a of o)removeEventListener(a,i);Ot=null},c=setTimeout(i,5e3);for(let a of o)addEventListener(a,i,{passive:!0});Ot=i}var zt=["failed","killed","lost"],Gr={icon:"eye-off",tone:"muted",label:"Hidden"},qr="Hidden: left out of tables, counts and checks until promoted";function Bt(e){let t=Me(e.path),n=t==="."?e.path:e.path.slice(t.length+1),s=q(e.path)?[]:n.split("/"),o=s.length&&ie(s[s.length-1])?s[s.length-1]:null,i=s.slice(0,-1),c=a=>[...t==="."?[]:[t],...i.slice(0,a+1)].join("/");return r`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${s.length?r`<a href=${E(t)}>${t==="."?"local":t}</a>`:null}
      ${i.map((a,l)=>r`<span>/</span><a href=${E(c(l))}>${a}</a>`)}
    </nav>
    ${o?r`<${Zr} id=${o} scope=${e.path} />`:r`<${Xr} path=${e.path} />`}
    ${e.finding?r`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function Xr({path:e}){let t=L(k(Ie(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return r`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let s=M(U),o=s.page==="group"&&s.hiddenRuns,i=Object.entries(k({method:"keys",params:{from:e},scope:e}).data?.codes??{}),c=zt.reduce((a,l)=>a+(t[l]??0),0);return r`
    <h1 class="page-title title" tabindex="-1">${n} <${O} spec=${_("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?r`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?r`<span><b>${t.finished}</b> finished</span>`:null}
      ${c?r`<span class="tone-bad" data-tip=${zt.filter(a=>t[a]).map(a=>`${t[a]} ${a}`).join(", ")}>
            <${x} name="circle-x" size=${15} /> <b>${c}</b> ${c===1?zt.find(a=>t[a]):"ended early"}</span>`:null}
      ${i.length?r`<span data-tip=${i.map(([a,l])=>`${a}: ${l} run${l===1?"":"s"}`).join(", ")}>
            <${x} name="git-commit" size=${15} /> <b>${i.length}</b> code versions</span>`:null}
      ${t.hidden?r`<span><a href=${E(e,{hidden:!o})} data-tip=${o?"Close the list of hidden runs":"List the hidden runs"}>
            <${x} name="eye-off" size=${15} /> <b>${t.hidden}</b> hidden</a></span>`:null}
      ${t.notes?r`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${Ps} path=${e} />
    </p>`}function Ms({path:e}){let t=L(k(ss(e)).data);return t.length?r`<${B} label="hidden runs">
    <table class="runs">
      <thead><tr class="small"><th>run</th><th>status</th><th>created</th><th></th></tr></thead>
      <tbody>${t.map(n=>r`<tr key=${n["run.id"]}>
        <td><a href=${re(n["run.id"],e)}>${n["run.name"]??n["run.id"]}</a></td>
        <td><${O} spec=${Ge(n["run.status"],null)} word /></td>
        <td class="muted" data-tip=${n["run.created_at"]}>${W(n["run.created_at"])}</td>
        <td><${Q} icon="eye" kind="quiet" onClick=${()=>Rt(n["run.id"],e)}>Promote<//></td>
      </tr>`)}</tbody>
    </table>
  <//>`:null}function Ds({path:e}){let t=L(k(Ie(e)).data)[0]??null,n=k(t?.proposal?Qn(e):null).data,s=k(t?.proposal?es(e):null).data;if(!t?.proposal)return null;let o=s?.proposal?.rationale,i=s?.versions?.find(l=>l.version===s.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[c,a]=It(n?.progress?.text??t.progress);return r`<${B} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${Se} value=${t.proposal} label="the proposal's statement" locked=${s?i:"Loading the proposal\u2026"}
          render=${l=>r`<span data-tip=${i?void 0:o}>${l}</span>`}
          onSave=${l=>qn(e,l)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(l=>{let u=_("result",l.result),$=Cn(l),d=$?`${u.label}: ${$}`:u.label;return r`<span class=${`check small tone-${u.tone}`} key=${l.name} data-tip=${d}
              aria-label=${`${l.name}: ${d}`} tabindex="0"><${x} name=${u.icon} size=${14} />${l.name}</span>`})}
        ${n?.provisional||c?r`<span class="small">
              ${n?.provisional?r`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${c?r`<span class="muted" data-tip=${a}>${n?.provisional?" \xB7 ":""}${c}</span>`:null}
            </span>`:null}
      </div>
      <${Yr} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function Yr(e){let t=k(e.verdict?pt(e.path):null).data;if(!e.verdict)return r`<p class="verdict-line muted">no verdict yet</p>`;let n=_("verdict",e.verdict),s=(t?.entries??[]).find(i=>i.type==="verdict"&&(i.group??e.path)===e.path),o=s?ke(s.id):null;return r`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${x} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${s?r`<span class="small muted" data-tip=${o}>verdict${s.meta?.author?` by ${s.meta.author}`:""}${o?` \xB7 ${W(o)}`:""}</span>`:null}
  </p>`}function Zr({id:e,scope:t}){let n=k(Oe(e,t)).data;if(!n)return r`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let s=n.run,o=()=>{navigator.clipboard?.writeText(s.id)},i=()=>{Rt(s.id,t)};return r`
    <h1 class="page-title title" tabindex="-1"><${Se} value=${s.name??s.id} label="the run's name" class="title-edit"
        onSave=${c=>Yn(s.id,t,c.trim())} />
      <${O} spec=${Ge(s.status,s.exit)} word tip=${et(s)} />
      ${s.hidden?r`<${O} spec=${Gr} word tip=${qr} />`:null}</h1>
    ${s.error?r`<p class="bad-text" data-tip=${s.error}>${s.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${de(s.steps)}</b> steps</span>
      <span><b>${Te(s.duration_s)}</b></span>
      ${n.progress?r`<${Jr} run=${s} progress=${n.progress} />`:null}
      <span data-tip=${s.created_at}>${W(s.created_at)}</span>
      <${Ps} path=${t} />
      ${s.hidden?r`<${I} icon="eye" label="Promote: count this run in tables, charts and checks" onClick=${i} />`:null}
      <${I} icon="copy" label=${`Copy the run id ${s.id}`} onClick=${o} />
      <${it} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${[...Qr(s),...yt(n)].map(([c,a])=>r`<tr><td class="muted">${c}</td><td>${a}</td></tr>`)}</table>
        ${s.git?.dirty?r`<${wt} run=${s.id} scope=${t} />`:null}
        <div class="menu-list">
          <button type="button" onClick=${()=>R(E(t,{run:s.id}),{replace:!0})}>
            <${x} name="panel-right" size=${15} /> Open in the side panel</button>
          ${s.hidden?r`<button type="button" onClick=${i}><${x} name="eye" size=${15} /> Promote</button>`:null}
          <button type="button" onClick=${o}><${x} name="copy" size=${15} /> Copy the run id</button>
          ${s.git?.commit?r`<button type="button" onClick=${()=>navigator.clipboard?.writeText(s.git.commit)}>
            <${x} name="git-commit" size=${15} /> Copy the commit</button>`:null}
        </div>
      <//>
    </div>
    ${(n.proposals??[]).length?r`<div class="checks">
          ${n.proposals.map(c=>{let a=_("result",c.check);return r`<a class=${`check small tone-${a.tone}`} href=${E(c.group)} data-tip=${c.statement}>
              <${x} name=${a.icon} size=${14} />${c.group==="."?"own proposal":c.group}
              ${c.verdict?r`<${O} spec=${_("verdict",c.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function Jr({run:e,progress:t}){let{epoch:n,total:s,fraction:o,steps_per_epoch:i}=t,c=e.status==="running"&&o!==null&&i&&e.steps_per_s?Te((1-o)*s*i/e.steps_per_s):null;return r`<span>epoch <b>${n}</b>${s?` of ${s}`:""}${o===null?"":` \xB7 ${Math.round(o*100)} % through`}${c?` \xB7 about ${c} left`:""}</span>`}function Ps({path:e}){let t=se(e).main,n=kt(Lt(e,t),e).data?.summary;if(!n)return null;let s=Object.entries(n.config??{}).map(([c,a])=>`${Be(c)} ${G(a)}`).join(", "),o=ie(e.split("/").pop()??""),i=`${n.stat} of ${n.metric} over ${o?"the run":"all runs"}${s?` (${s})`:""}`;return r`<span data-tip=${i}>
    best <b>${n.label??Be(`metric.${n.metric}.${n.stat}`)} ${G(n.value)}</b>
    ${o?null:r` · <a href=${re(n.run)}>${n.name}</a>`}
  </span>`}function Qr(e){return[["id",e.id],["host",e.host],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,s])=>[n,String(s)])}var At=80;function Ns({node:e}){let t=J("main"),n=J(e.data?.keys?"keys":""),s=e.props.mode==="run",o=e.props.title??(s?"Config":"Hyperparameters");return r`<${We} id=${`config:${e.id}`} title=${o} open=${e.props.open} result=${t}>
    ${t.data?s?r`<${ct} config=${t.data.config} varying=${qe(n.data)} />`:r`<${eo} rows=${t.data.config?.rows??[]} />`:r`<div class="skeleton late" style="block-size: 80px"></div>`}
  <//>`}function eo({rows:e}){let t=new Set(qe({config:{rows:e}})),n=e.filter(([s])=>t.has(s.replace(/^config\./,"")));return n.length?r`<table class="kv small">${n.map(([s,,o])=>{let i=Array.isArray(o)?o.map(G).join(", "):`${G(o.min)} \u2026 ${G(o.max)} \xB7 ${o.distinct} values`;return r`<tr><td data-tip=${s}>${s.replace(/^config\./,"")}</td>
      <td data-tip=${i.length>At?i:void 0}>${i.length>At?`${i.slice(0,At-1)}\u2026`:i}</td></tr>`})}</table>`:r`<p class="muted small">No config differs between the runs.</p>`}var Rs=15e3;function Ls({node:e}){let t=Z(F),n=me(),[s,o]=wn(),i=e.props.code,c=k(o&&i?{method:"code",params:i,scope:null}:null),[a,l]=y(null),[u,$]=y(120),[d,m]=y({error:null,warnings:[]}),f=w=>{le&&console.error(`[block ${e.id}] ${w}`),m(p=>({...p,error:w}))},g=N(()=>{});T(()=>{if(!a)return;m(v=>v.own?{...v,own:!1}:v);let w=!0;Ke.n++;let p=()=>{w&&Ke.n--,w=!1};g.current=p;let b=setTimeout(()=>{w&&f(`no first render within ${Rs/1e3} s`),p()},Rs);return()=>{clearTimeout(b),p()}},[a]),T(()=>{let w=a?.contentWindow;if(!w||c.status!=="ready")return;let p=P=>w.postMessage(P,"*"),b=new Map,v=new Pn,H=P=>{if(P.source!==w)return;let S=P.data;switch(S.type){case"hello":p({type:"init",init:{id:e.id,code:c.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:yn.value,pair:st.value,colormaps:Fe.value,prefs:Ae(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics,expanded:e.props.expanded?En():null}});break;case"sub":if(!Tn.has(S.call.method)){p({type:"result",id:S.id,result:{status:"error",data:null,error:`${S.call.method} is not available in a custom block`,refreshing:!1}});break}b.get(S.id)?.(),b.set(S.id,ln(S.call,ne=>p({type:"result",id:S.id,result:ne})));break;case"unsub":b.get(S.id)?.(),b.delete(S.id);break;case"navigate":S.url.startsWith("/")&&R(S.url);break;case"height":v.accept(performance.now())?$(Math.max(40,S.height)):K("its height keeps changing, so it is fixed at its last height");break;case"chrome":m(ne=>({...ne,own:S.own}));break;case"ready":m(ne=>({...ne,blank:S.blank,overflow:S.overflow})),g.current();break;case"warn":K(S.message);break;case"hover":De.set(S.run);break;case"prefs":JSON.stringify(A.value)!==JSON.stringify(S.prefs)&&A.set(S.prefs);break;case"download":case"snapshot":S.href?Mn(S.href,S.name)?performance.now()-V>1e3&&(V=performance.now(),be().download(S.href,S.name)):K(`a download of ${S.name} was refused: only PNG, SVG and CSV files`):K("it draws no SVG or canvas to download");break;case"figure":be().figure(S.spec,S.name).catch(ne=>K(`the PDF failed: ${ne.message}`));break;case"expand":Dn(S.node)&&be().expand(S.node,t);break;case"expand-block":e.props.expanded||be().expand(e,t);break;case"close":e.props.expanded&&Le.set(null);break;case"error":f(S.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,C)),g.current();break;default:break}},K=P=>{le&&console.warn(`[block ${e.id}] ${P}`),m(S=>S.warnings.includes(P)?S:{...S,warnings:[...S.warnings,P]})},V=-1/0,A=Ae(t.path),Y=De.subscribe(P=>p({type:"hover",run:P})),D=A.subscribe(P=>p({type:"prefs",prefs:P}));return addEventListener("message",H),p({type:"ping"}),()=>{Y(),D(),removeEventListener("message",H);for(let P of b.values())P()}},[c.status,c.data?.code,a]),T(()=>{let w={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};a?.contentWindow?.postMessage(w,"*")},[t.names,t.colors,t.metrics,a]),T(()=>Fe.subscribe(w=>a?.contentWindow?.postMessage({type:"colormaps",colormaps:w},"*")),[a]),T(()=>{n&&a?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let C=typeof i=="object"?i.path??i.block:String(i??"");kn(e.id,{png:()=>a?.contentWindow?.postMessage({type:"snapshot"},"*")});let h=o&&c.status==="ready"&&!d.error;return r`<div ref=${s} class="custom-block">
    ${d.own?null:r`<div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${h?r`<span class="chart-tools">
            <${I} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>a?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?r`<${I} icon="x" label="Close (Esc)" onClick=${()=>Le.set(null)} />`:r`<${I} icon="maximize" label="Expand" onClick=${()=>be().expand(e,t)} />`}
          </span>`:null}
    </div>`}
    <${oe} caption=${e.props.expanded?void 0:e.props.caption} result=${c}>
      ${d.error?r`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${C})</span>
            <pre class="code">${d.error}</pre>
          </div>`:null}
      ${d.warnings.map(w=>r`<${z} kind="warning">${w}<//>`)}
      ${h?r`<div class="custom-frame" data-frame-blank=${d.blank?"1":void 0} data-frame-overflow=${d.overflow?"1":void 0}>
            <iframe key=${c.data.code} ref=${l} sandbox="allow-scripts" ...${to()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${u}px`} />
          </div>`:null}
    <//>
  </div>`}function to(){if(!!1)return{src:en("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1").replace(/@font-face\s*\{[^}]*\}/g,""),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}function Ht(e,t){let n=e?.steps??[];if(t==="step")return{values:n,steps:n};let s=new Map;n.forEach((i,c)=>{let a=e?.clocks?.[c];a!=null&&Number.isFinite(a)&&s.set(a,Math.max(s.get(a)??i,i))});let o=[...s.keys()].sort((i,c)=>i-c);return{values:o,steps:o.map(i=>s.get(i))}}function Kt(e){return Ht(e,"clock").values.length>1}function _s(e,t){let n=0;return e.forEach((s,o)=>{Math.abs(s-t)<Math.abs(e[n]-t)&&(n=o)}),n}function Is(e,t){let n=0;return e.steps.forEach((s,o)=>{s<=t&&(n=o)}),n}function Os(e,t){let n=new Map;for(let s of e)s.step<=t&&s.step>(n.get(s.run)??-1/0)&&n.set(s.run,s.step);return e.filter(s=>n.get(s.run)===s.step).map(s=>({entry:s,earlier:s.step<t&&t!==1/0}))}function zs(e){return e.reduce((t,n)=>!t||n.entry.step>t.entry.step?n:t,void 0)}function Bs(e,t,n){let s=e?.split(/[/.]/).at(-1);return[...s&&s!=="step"&&t!=null?[`${s} ${G(t)}`]:[],`step ${de(n)}`].join(" \xB7 ")}function As(e,t){let n=e?.steps?.indexOf(t)??-1;return n<0?null:e?.clocks?.[n]??null}var Ut={k:1,x:0,y:0},Hs=32;function Ks(e,t,n){let s=Math.min(Hs,Math.max(1,e.k));return{k:s,x:Math.min(0,Math.max(t*(1-s),e.x)),y:Math.min(0,Math.max(n*(1-s),e.y))}}function no(e,t,n,s,o,i){let c=Math.min(Hs,Math.max(1,e.k*t)),a=c/e.k;return Ks({k:c,x:n-(n-e.x)*a,y:s-(s-e.y)*a},o,i)}function so(e,t,n,s,o){return Ks({...e,x:e.x+t,y:e.y+n},s,o)}function Us(e){return`translate(${e.x}px, ${e.y}px) scale(${e.k})`}function Fs(){let e=N(null),[t,n]=y(Ut),s=()=>{let a=e.current.getBoundingClientRect();return{w:a.width,h:a.height,left:a.left,top:a.top}},o=(a,l)=>{let{w:u,h:$}=s();n(d=>no(d,a,l?.x??u/2,l?.y??$/2,u,$))};T(()=>{let a=e.current;if(!a)return;let l=u=>{u.preventDefault();let{left:$,top:d}=s();o(Math.exp(-u.deltaY*(u.ctrlKey?.01:.002)),{x:u.clientX-$,y:u.clientY-d})};return a.addEventListener("wheel",l,{passive:!1}),()=>a.removeEventListener("wheel",l)},[]);let i=N(new Map);return{box:e,pose:t,handlers:{onPointerDown:a=>{a.currentTarget.setPointerCapture(a.pointerId),i.current.set(a.pointerId,{x:a.clientX,y:a.clientY})},onPointerMove:a=>{let l=i.current.get(a.pointerId);if(!l)return;let u={x:a.clientX,y:a.clientY},{w:$,h:d,left:m,top:f}=s(),g=[...i.current.entries()].filter(([C])=>C!==a.pointerId).map(([,C])=>C);if(i.current.set(a.pointerId,u),g.length){let[C]=g,h=Math.hypot(l.x-C.x,l.y-C.y),w=Math.hypot(u.x-C.x,u.y-C.y);h>0&&o(w/h,{x:(u.x+C.x)/2-m,y:(u.y+C.y)/2-f})}else n(C=>so(C,u.x-l.x,u.y-l.y,$,d))},onPointerUp:a=>{i.current.delete(a.pointerId)},onPointerCancel:a=>{i.current.delete(a.pointerId)},onDblClick:()=>n(Ut)},zoomBy:o,fit:()=>n(Ut)}}var Ft=new Map;function ro(e,t){return Ft.has(e)||Ft.set(e,new fe({step:t,by:"step"})),Ft.get(e)}function oo(e,t){let[n,s]=y(e);return T(()=>{let o=setTimeout(()=>s(e),t);return()=>clearTimeout(o)},[e]),n}function ao(e){let t=Z(F),n=e.data.main,s=n.params.step,o=`${t.path}\0${e.id}`,i=ro(o,typeof s=="number"?s:null),c=M(i),a=k(n),l=a.data?.meta,u=c.by==="clock"&&Kt(l)?"clock":"step",$=Ee(()=>Ht(l,u),[l,u]),d=c.step===null,m=!(le||!1)&&(s==="last"||typeof s=="number")&&$.steps.length>1,f=d?$.steps.length-1:Is($,c.step),g=$.steps[f]??0,C=N(null),h=oo(g,120),w=C.current?h:g,p=m&&(!d||s!=="last"),b=p?{...n,params:{...n.params,step:["last",w],limit:2e3}}:null,v=k(b),H=p?v.data:a.data;H&&(C.current={entries:H.entries,at:p?w:1/0});let K=s!=="last"&&typeof s!="number",V=C.current?K?C.current.entries.map(D=>({entry:D,earlier:!1})):Os(C.current.entries,C.current.at):[],A=n.params.clock??null,Y=D=>{let P=Math.min($.steps.length-1,Math.max(0,D));i.set({...c,step:P===$.steps.length-1?null:$.steps[P]})};return{view:t,base:a,error:v.status==="error"?String(v.error):null,tiles:V,stops:$,i:f,ranged:m,by:u,move:Y,clock:A,label:Bs(A,As(l,g),g),clocked:Kt(l),setBy:D=>i.set({step:d?null:g,by:D})}}function io(e,t,n){let s=t.path.split(".").at(-1);return[Qe(pe(t.run,e.path),t.path),`${t.run}-${n.replace(/[^\w.-]+/g,"_")}-step${t.step}.${s}`]}function Ws(e,t,n){for(let{entry:s}of t)be().download(...io(e,s,n))}function js(e,t,n,s){return{files:[{label:s,save:()=>n&&Ws(e.view,[n],t)},{label:`All images (${e.tiles.length})`,save:()=>Ws(e.view,e.tiles,t)}]}}function Vs({s:e}){if(!e.ranged)return null;let{values:t}=e.stops,n={ArrowLeft:e.i-1,ArrowDown:e.i-1,ArrowRight:e.i+1,ArrowUp:e.i+1,Home:0,End:t.length-1};return r`<div class="scrubber">
    <input type="range" min=${t[0]} max=${t.at(-1)} step="any" value=${t[e.i]} aria-label="Step" aria-valuetext=${e.label}
      onInput=${s=>{let o=s.target,i=_s(t,Number(o.value));o.value=String(t[i]),e.move(i)}}
      onKeyDown=${s=>{s.key in n&&(s.preventDefault(),e.move(n[s.key]))}} />
    <span class="small scrub-label">${e.label}</span>
  </div>`}function Gs({s:e}){if(!e.ranged||!e.clocked)return null;let t=e.clock?.split(/[/.]/).at(-1)??"clock";return r`<button type="button" class="small tool-toggle" aria-pressed=${e.by==="clock"} data-tip=${`Space the stops by ${t}`}
    onClick=${()=>e.setBy(e.by==="clock"?"step":"clock")}>by ${t}</button>`}function qs({node:e}){let t=ao(e),n=String(e.props.title??e.data.main.params.key);if(e.props.expanded)return r`<${lo} node=${e} s=${t} title=${n} />`;let s=o=>be().expand({...e,props:{...e.props,run:o??t.tiles[0]?.entry.run}},t.view);return r`<div class="block chart-block images-block">
    <${Pt} id=${e.id} title=${n} caption=${e.props.caption}
      tools=${r`<${Gs} s=${t} />`}
      downloads=${js(t,n,zs(t.tiles),"Latest image")} onExpand=${()=>s()}>
      ${t.base.status==="error"?r`<${z} kind="error">${t.base.error}<//>`:null}
      ${t.error?r`<${z} kind="error">${t.error}<//>`:null}
      ${t.base.data&&!t.tiles.length?r`<${z}>No images logged.<//>`:null}
      <div class="images">
        ${t.tiles.map(({entry:o,earlier:i})=>r`<figure key=${`${o.run}/${o.path}`} class=${i?"earlier":""} data-tip=${t.view.names.get(o.run)??o.run}>
            <button type="button" class="image-open" aria-label="Open larger" onClick=${()=>s(o.run)}>
              <img src=${Qe(pe(o.run,t.view.path),o.path)} alt=${o.caption??n} loading=${Ue?"eager":"lazy"} />
            </button>
            <figcaption class="small">step ${de(o.step)}${o.caption?` \xB7 ${o.caption}`:""}</figcaption>
          </figure>`)}
      </div>
      <${Vs} s=${t} />
    <//>
  </div>`}function lo({node:e,s:t,title:n}){let{tiles:s}=t,[o,i]=y(e.props.run),c=Fs(),a=Math.max(0,s.findIndex(f=>f.entry.run===o)),l=s[a],u=l?Qe(pe(l.entry.run,t.view.path),l.entry.path):"";T(()=>c.fit(),[u]);let $=f=>i(s[(a+f+s.length)%s.length].entry.run),d={"+":()=>c.zoomBy(1.5),"=":()=>c.zoomBy(1.5),"-":()=>c.zoomBy(1/1.5),0:c.fit},m=r`
    ${s.length>1?r`<${I} icon="chevron-left" label="Previous image" onClick=${()=>$(-1)} /><${I} icon="chevron-right" label="Next image" onClick=${()=>$(1)} />`:null}
    <${I} icon="minus" label="Zoom out (−)" onClick=${()=>c.zoomBy(1/1.5)} />
    <${I} icon="plus" label="Zoom in (+)" onClick=${()=>c.zoomBy(1.5)} />
    <${I} icon="reset" label="Fit (double-click, 0)" onClick=${c.fit} />
    <${Gs} s=${t} />`;return r`<div class="block chart-block images-block">
    <${Pt} id=${e.id} title=${n} expanded
      notes=${l?[t.view.names.get(l.entry.run)??l.entry.run,`step ${de(l.entry.step)}`]:[]}
      tools=${m} downloads=${js(t,n,l,"This image")}>
      <div class="zoom-box" ref=${c.box} tabindex="0" style=${{touchAction:"none"}} ...${c.handlers}
        onKeyDown=${f=>d[f.key]?.()}>
        ${l?r`<img class="zoom-img" src=${u} alt=${l.entry.caption??n} draggable=${!1} style=${{transform:Us(c.pose)}} />`:null}
      </div>
      <${Vs} s=${t} />
    <//>
  </div>`}function Xs({node:e}){let t=J("main"),n=t.data?.entries??[];return r`<${oe} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?r`<${z}>No text logged.<//>`:null}
    ${n.map(s=>r`<div class="text-entry" key=${`${s.run}/${s.step}`}>
        <div class="muted small">step ${de(s.step)}${s.caption?` \xB7 ${s.caption}`:""}</div>
        <pre class="code">${s.text??""}</pre>
      </div>`)}
  <//>`}function Ys({node:e}){let n=`section.${Z(F).path}:${e.id}`,[s,o]=y(()=>Ue||xe(n,e.props.open!==!1)),i=()=>{he(n,!s),o(!s)},c=r`${(e.children??[]).map(u=>r`<${ue} key=${u.id} node=${u} />`)}`,a=Z(at);if(!e.props.title)return r`<div class="stack">${c}</div>`;let l=a===e.props.title.toLowerCase();return r`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${s} aria-label=${l?`${s?"Close":"Open"} ${e.props.title}`:void 0}
        data-tip=${l?`${s?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${i}>
      <${x} name=${s?"chevron-down":"chevron-right"} size=${16} />${l?r`<span class="toggle-label code">${a}</span>`:e.props.title}
    </button>
    ${s?r`<div class="stack">${c}</div>`:null}
  </div>`}function Zs({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return r`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>r`<${ue} key=${n.id} node=${n} />`)}
  </div>`}function jt({node:e,after:t}){let n=Z(F),s=se(n.path),o=e.props.min_width??320,i=e.props.columns,c=i?`grid-template-columns: repeat(${i}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${o}px, 100%), 1fr))`,a=e.children??[],l=a.filter(d=>s.removed.includes(d.id)).map(d=>d.id),u=an(a.filter(d=>!l.includes(d.id)),s.order[e.id]),$=(d,m)=>{let f=u.map(g=>g.id).filter(g=>g!==d);if(f.splice(f.indexOf(m),0,d),rn(n.path,e.id,f),e.id===tn){let g=h=>a.find(w=>w.id===h)?.data?.main?.params?.y?.[0],C=f.map(h=>n.pins.find(w=>w.y===g(h))).filter(h=>!!h);sn(n.path,[...C,...n.pins.filter(h=>!C.includes(h))])}};return r`<div class="grid" style=${c}>
    ${u.map(d=>r`<${co} key=${d.id} node=${d} path=${n.path} span=${s.spans[d.id]??d.props.span??1}
      columns=${i} onDrop=${m=>m!==d.id&&$(m,d.id)} />`)}
    ${t??null}
    ${l.length?r`<div class="grid-note"><button type="button" class="link small" onClick=${()=>He(n.path,l)}>${l.length} hidden · show</button></div>`:null}
  </div>`}var Wt=[1,2,"full"];function co(e){let[t,n]=y(!1),s=Wt[(Wt.indexOf(e.span)+1)%Wt.length],o=i=>i==="full"?"full width":`${i} column${i===1?"":"s"}`;return r`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${i=>{i.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${i=>{i.preventDefault(),n(!1),e.onDrop(i.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${i=>i.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${x} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${o(e.span)}; click for ${o(s)}`}
        aria-label=${`Width ${o(e.span)}`} onClick=${()=>on(e.path,e.node.id,s)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${ue} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function Vt({root:e}){let t=Z(F),n=se(t.path),s=k({method:"keys",params:{from:t.path},scope:t.path}).data,o=e.props.template;if(!o||!1)return null;let i=new Set(n.removed),c=new Set([...t.charted].filter(([f])=>!i.has(f)).flatMap(([,f])=>f)),a=n.added.filter(f=>!c.has(f)).map(f=>({block:"line",id:`added-${f}`,props:{y:f},data:{main:{...o,params:{...o.params,y:[f]}}}})),l=new Set([...c,...a.filter(f=>!i.has(f.id)).map(f=>f.props.y)]),u=(s?.metrics?.rows??[]).map(f=>f[0]).filter(f=>!l.has(f));if(!s||!(u.length||a.length))return null;let $=f=>[...t.charted].find(([g,C])=>i.has(g)&&C.includes(f))?.[0]??a.find(g=>i.has(g.id)&&g.props.y===f)?.id,d=f=>{let g=$(f);g?He(t.path,[g]):tt(t.path,C=>({added:[...C.added,f]}))},m=u.length?r`<div class="add-chart">
        <span class="add-chart-label"><${x} name="plus" size=${16} /> Add a chart</span>
        <${lt} single options=${u} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
          onChange=${([f])=>d(f)} />
      </div>`:null;return r`<${B}><${jt} node=${{block:"grid",id:"added",props:{},children:a}} after=${m} /><//>`}function Js({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[s,o]=y(()=>t.find(a=>a.id===n())?.id??t[0]?.id),i=a=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(a)}`),o(a)},c=t.find(a=>a.id===s)??t[0];return Ue?r`<div class="stack">${t.map(a=>r`<${ue} key=${a.id} node=${a} />`)}</div>`:r`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(a=>r`<button type="button" role="tab" id=${`tab-${a.id}`} aria-selected=${a.id===c?.id}
          aria-controls=${`panel-${a.id}`} onClick=${()=>i(a.id)}>${a.props.title??a.id}</button>`)}
    </div>
    ${c?r`<div class="stack" role="tabpanel" id=${`panel-${c.id}`} aria-labelledby=${`tab-${c.id}`}>
          ${(c.children??[]).map(a=>r`<${ue} key=${a.id} node=${a} />`)}
        </div>`:null}
  </div>`}function Qs({node:e}){let t=J("main"),n=Z(F),s=M(De),o=e.props,i=Nn(t.data,o.rows,o.columns,o.lower??{},o.expected??[]),c=U.value.page==="group"?U.value.run:null,a=o.baseline===null||o.baseline===void 0?null:i.find(u=>u.label===String(o.baseline)),l=u=>R(E(n.path,{run:u}),{replace:c!==null});return r`<${oe} title=${o.title} caption=${o.caption} numbered result=${t}>
    ${t.data?r`<div class="table-wrap"><table class="runs scorecard">
          <thead><tr class="small">
            <th data-tip=${o.rows}>${Be(o.rows)}</th>
            ${o.columns.map(u=>r`<th class="num" data-tip=${u}>${On(u,n.metrics)}</th>`)}
          </tr></thead>
          <tbody onPointerLeave=${()=>De.set(null)}>
            ${i.map(u=>{let $=`${u.runs.includes(c??"")?"selected":""}${u.runs.includes(s??"")?" hovered":""}${u.queued?" queued":""}`;return r`<tr key=${u.label} class=${$} data-tip=${u.runs.length?`${u.runs.length} run${u.runs.length>1?"s":""}`:void 0}
                  onClick=${u.runs.length?()=>l(u.runs[0]):void 0}
                  onPointerEnter=${()=>De.set(u.runs[0]??null)}>
                <td>${u.label}${u===a?r` <${Ce} tip="the others are compared to this row">baseline<//>`:null}${u.queued?r` <${Ce}>queued<//>`:null}</td>
                ${u.scores.map((d,m)=>uo(d,u.live,a?.scores[m]??null))}
              </tr>`})}
          </tbody>
        </table></div>`:r`<div class="skeleton late" style="block-size: 120px"></div>`}
  <//>`}function uo(e,t,n){if(!e)return r`<td class="num muted">–</td>`;let s=n&&n!==e?`${e.mean-n.mean>=0?"+":"\u2212"}${G(Math.abs(e.mean-n.mean))} against the baseline`:"",o=`${St(e.mean)}${e.std===null?"":` \xB1 ${St(e.std)}`}, ${e.n} run${e.n>1?"s":""}${s?`. ${s}`:""}`,i=`num score${e.best?" best":""}${t?" live":""}`;return r`<td class=${i} style=${e.shade===null?void 0:`--shade: ${e.shade}`} data-tip=${o}>
    ${G(e.mean)}${e.std===null?null:r`<span class="spread"> ± ${G(e.std)}</span>`}</td>`}var er={section:Ys,row:Zs,grid:jt,line:An,table:Wn,scorecard:Qs,stat:Fn,images:qs,text:Xs,proposal:gs,note:Ss,output:xs,config:Ns,memory:bs,groups:vs,notes:ys,tabs:Js,scatter:Hn,bar:Kn,histogram:Un,data_table:_n,timeline:In,custom:Ls,markdown:Cs},po=new Set(["line","scatter","bar","histogram"]);function ue({node:e}){return po.has(e.block)?r`<${mo} node=${e} />`:r`<${Dt} node=${e} blocks=${er} />`}function mo({node:e}){let t=Z(F);return se(t.path).removed.includes(e.id)?r`<div class="grid-note"><button type="button" class="link small" onClick=${()=>He(t.path,[e.id])}>1 hidden · show</button></div>`:r`<${Dt} node=${e} blocks=${er} />`}function tr(e,t){let n=e.split(`
`),s=t.split(`
`),o=n.length,i=s.length,c=Array.from({length:o+1},()=>new Uint32Array(i+1));for(let $=o-1;$>=0;$--)for(let d=i-1;d>=0;d--)c[$][d]=n[$]===s[d]?c[$+1][d+1]+1:Math.max(c[$+1][d],c[$][d+1]);let a=[],l=0,u=0;for(;l<o&&u<i;)n[l]===s[u]?(a.push({kind:"same",text:n[l]}),l++,u++):c[l+1][u]>=c[l][u+1]?a.push({kind:"removed",text:n[l++]}):a.push({kind:"added",text:s[u++]});for(;l<o;)a.push({kind:"removed",text:n[l++]});for(;u<i;)a.push({kind:"added",text:s[u++]});return a}function nr(e,t=3){let n=[],s=0;for(;s<e.length;){if(e[s].kind!=="same"){n.push(e[s++]);continue}let o=s;for(;o<e.length&&e[o].kind==="same";)o++;let i=s===0?0:t,c=o===e.length?0:t;o-s>i+c+1?n.push(...e.slice(s,s+i),{kind:"skip",count:o-s-i-c},...e.slice(o-c,o)):n.push(...e.slice(s,o)),s=o}return n}var Gt={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",config:"config",timeline:"timeline",proposal:"predictions"};function sr(e){if(Gt[e.block])return Gt[e.block];if(e.block==="row"||e.block==="grid"){let n=new Set((e.children??[]).map(o=>Gt[o.block])),[s]=n;if(n.size===1&&s)return s}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function xt(e){let t=k(Xe(e.path)),n=me(),s=L(t.data),o=Ee(()=>ot(s.map(m=>m["run.id"]),n),[t.data,n]),i=Ee(()=>new Map(s.map(m=>[m["run.id"],m["run.name"]??m["run.id"]])),[t.data]),c=se(e.path),a=e.plain?"view plain":"sections view";if(!e.view)return r`<div class=${a}>${e.before}
      ${e.plain?r`<div class="skeleton late" style="block-size: 320px"></div>`:r`<${B} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let l=e.view.view,u={path:e.path,colors:o,names:i,metrics:e.view.metrics??{},charted:qt(l),pins:c.main??e.view.pins??[]};if(e.plain)return r`<div class=${a}><${F.Provider} value=${u}><${ue} node=${l} /><//></div>`;let $=l.block==="section"&&!l.props.title?l.children??[]:[l],d=$.map(m=>qt(m).size>0).lastIndexOf(!0);return r`<div class=${a}>${e.before}
    <${F.Provider} value=${u}>
      ${$.map((m,f)=>{let g=sr(m);return r`<${Zt} key=${m.id}><${B} label=${g}><${at.Provider} value=${g}><${ue} node=${m} /><//><//>
          ${f===d?r`<${Vt} root=${l} />`:null}<//>`})}
      ${d===-1?r`<${Vt} root=${l} />`:null}
    <//>
  </div>`}function qt(e,t=new Map){e.block==="line"&&t.set(e.id,e.data?.main?.params?.y??[]);for(let n of e.children??[])qt(n,t);return t}function rr(e){if(null)return r`<div class="view-source small"><${x} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=M(U),s=n.page==="group"&&n.version,o=t.versions?r`<a href=${E(e.path,{history:!0})}><${x} name="history" size=${14} /> history (${t.versions})</a>`:null,i;switch(t.source){case"draft":i=r`draft <b>${t.draft}</b>`;break;case"view":i=r`${t.title?r`<em>${t.title}</em> · `:null}saved ${W(ke(t.version))} by ${t.author??"unknown"}`;break;default:i=r`the built-in view`}return r`<div class="view-source small">
    <${x} name="layout" size=${14} /><span>${i}</span>
    ${s?r`<a href=${E(e.path)}>an older version · show the current one</a>`:null}
    ${o}
    ${t.outdated?.length&&!s?r`<${$o} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||s?null:r`<${fo} path=${e.path} />
        <${ho} path=${e.path} view=${t} />`}
  </div>`}function $o(e){let[t,n]=y(null),s=e.outdated.map(i=>i.name).join(", ");return r`<button type="button" class="link small" onClick=${async()=>{n(null);try{await Zn(e.path)}catch(i){n(i.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${s} exists; update re-pins this view to it (a new version)`}>
      <${x} name="update" size=${14} /> update ${s}</button>
    ${t?r`<span class="bad-text small">${t}</span>`:null}`}function fo(e){let[t,n]=y(null);return r`<button type="button" class="link small" onClick=${async()=>{n(null);try{_e.set(await dt(e.path,null,""))}catch(o){n(o.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${x} name="file-text" size=${14} /> add text</button>
    ${t?r`<span class="bad-text small">${t}</span>`:null}`}function ho(e){let t=se(e.path),n=nn(t),[s,o]=y(!1),[i,c]=y(e.view.title??""),[a,l]=y(e.view.finding??""),[u,$]=y(null),[d,m]=y(!1);if(!n&&!s)return null;let f=async g=>{g.preventDefault(),m(!0),$(null);try{let C={charts:t.charts,view:t.view,added:t.added,removed:t.removed,order:t.order,spans:t.spans,main:t.main};await j("save_view",{path:e.path,prefs:C,title:i,finding:a}),tt(e.path,()=>({view:{},charts:{},added:[],removed:[],order:{},spans:{},main:null})),Re(h=>["view","view_history","summary"].includes(h.method)&&h.scope===e.path),o(!1)}catch(C){$(C.message)}finally{m(!1)}};return s?r`<form class="save-form" onSubmit=${f}>
    <${je} label="Title"><input value=${i} onInput=${g=>c(g.target.value)} /><//>
    <${je} label="Finding"><input value=${a} placeholder="the key result in one sentence"
        onInput=${g=>l(g.target.value)} /><//>
    <div class="save-actions">
      <${Q} type="submit" icon=${d?"hourglass":"save"} disabled=${d}>${d?"Saving\u2026":"Save as view"}<//>
      <${Q} icon="x" kind="quiet" onClick=${()=>o(!1)}>Cancel<//>
      ${u?r`<span class="bad-text small">${u}</span>`:null}
    </div>
  </form>`:r`<${Q} icon="save" class="save-view" onClick=${()=>o(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function or(e){let t=k(is(e.path)),n=t.data?.entries??[],[s,o]=y(null),i=s??n.slice(0,2).map(a=>a.version).reverse(),c=a=>{let l=i.includes(a)?i.filter(u=>u!==a):[...i,a].slice(-2);o(l.sort())};return t.status==="error"?r`<${z} kind="error">${t.error}<//>`:r`<section class="history">
    ${t.data&&!n.length?r`<${z}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((a,l)=>r`<li key=${a.version} class=${i.includes(a.version)?"picked":""}>
          <label><input type="checkbox" checked=${i.includes(a.version)} onChange=${()=>c(a.version)} />
            <span class="num muted" data-tip=${a.version}>${W(a.time)}</span>
            <b>${a.title??"untitled"}</b><span class="muted">${a.author??""}</span>
            ${a.message?r`<span>${a.message}</span>`:null}</label>
          <a href=${l===0?E(e.path):E(e.path,{version:a.version})}
            onClick=${u=>{u.preventDefault(),R(l===0?E(e.path):E(e.path,{version:a.version}))}}>${l===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${i.length===2?r`<${go} path=${e.path} a=${i[0]} b=${i[1]} />`:null}
  </section>`}function go(e){let t=a=>({method:"view_show",params:{group:e.path,version:a},scope:e.path}),n=k(t(e.a)).data,s=k(t(e.b)).data,o=k(ve(e.path,e.a)).data,i=k(ve(e.path,e.b)).data,c=n&&s?nr(tr(n.yaml,s.yaml)):[];return r`<div class="compare">
    <h3 class="block-title heading">Changes from ${W(ke(e.a))} to ${W(ke(e.b))}</h3>
    <pre class="diff code">${c.map(a=>a.kind==="skip"?r`<div class="diff-skip">⋯ ${a.count} unchanged lines</div>`:r`<div class=${`diff-${a.kind}`}>${a.kind==="added"?"+ ":a.kind==="removed"?"\u2212 ":"  "}${a.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${o?.title??e.a}</h3><${xt} path=${e.path} view=${o} plain /></div>
      <div><h3 class="block-title heading">${i?.title??e.b}</h3><${xt} path=${e.path} view=${i} plain /></div>
    </div>
  </div>`}function ar(e){return ls(e.path),e.history?r`<div class="page"><div class="sections">
      <${B} label=${ir(e.path)}><${Bt} path=${e.path} /><//>
      <${B} label="history"><${or} path=${e.path} /><//>
    </div></div>`:r`<div class="page">
    <${bo} path=${e.path} version=${e.version??null} draft=${e.draft??null} hiddenRuns=${e.hiddenRuns??!1} />
  </div>`}function bo(e){let t=se(e.path).main,n=kt(ve(e.path,e.version,e.draft,t),`${e.path}|${e.version}|${e.draft}`);T(()=>{n.status==="ready"&&requestAnimationFrame($n)},[n.status==="ready"]),T(()=>{let o=i=>Ts(i.target.closest?.(".chart-frame")??null);return addEventListener("click",o,!0),()=>removeEventListener("click",o,!0)},[]);let s=r`
    <${B} label=${ir(e.path)}>
      <${Bt} path=${e.path} finding=${n.data?.finding} />
      ${n.data?r`<${rr} path=${e.path} view=${n.data} />`:null}
    <//>
    ${ie(e.path.split("/").pop()??"")?null:r`${e.hiddenRuns?r`<${Ms} path=${e.path} />`:null}<${Ds} path=${e.path} />`}`;return n.status==="error"?r`<div class="sections">${s}
      <${B} label="view">
        ${vo(e.path,n.error)?r`<${z} kind="warning">${n.error} The page fills in once the remote answers again.<//>`:r`<${z} kind="error">${n.error}<//>`}
      <//>
    </div>`:r`<${xt} path=${e.path} view=${n.data} before=${s} />`}function ir(e){return ie(e.split("/").pop()??"")?"run":"group"}function vo(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function lr(e){T(()=>{Ne(ve(e.id)).then(n=>R(E(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=k(ve(e.id));return t.status==="error"?r`<div class="page"><${z} kind="error">${t.error}<//></div>`:r`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var yo={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},Xt=20,ze=-1,wo=[["day",86400],["week",7*86400],["month",30*86400]];function ur(e){let t=L(k($e()).data).map(a=>a.path),n=k({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),s=k({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});Ze("Timeline",L(n.data).filter(a=>a["run.status"]==="running").length);let o=Date.now()/1e3,i=L(n.data).filter(a=>a["run.created_at"]).map((a,l)=>({id:a["run.id"],name:a["run.name"]??a["run.id"],group:a["run.group"],status:a["run.status"],start:Date.parse(a["run.created_at"])/1e3,end:a["run.ended_at"]?Date.parse(a["run.ended_at"])/1e3:o,lane:l})),c=(s.data?.entries??[]).map(a=>({id:a.id,type:a.type,group:a.group,description:a.description,t:Date.parse(ke(a.id))/1e3}));return r`<div class="page timeline-page"><div class="sections">
    <${B} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${je} label="Group" inline>
          <select value=${e.from} onChange=${a=>R(nt(a.target.value),{replace:!0})}>
            ${t.map(a=>r`<option value=${a}>${a==="."?"everything":a}</option>`)}
          </select><//>
        <span class="muted small">${i.length} runs · ${c.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${B} label="runs">
      ${n.status==="error"?r`<${z} kind="error">${n.error}<//>`:null}
      ${n.data&&s.data?r`<${ko} bars=${i} marks=${c} />`:r`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function ko(e){let t=me(),n=N(null),s=[...e.bars.flatMap(h=>[h.start,h.end]),...e.marks.map(h=>h.t)],o=s.length?cr(Math.min(...s),Math.max(...s)):cr(Date.now()/1e3-86400,Date.now()/1e3),[i,c]=y(o),a=e.bars.length,l=Math.min(900,Math.max(160,(a+1.5)*Xt+40)),$=zn(n,Bn,t?(h=>{let w=Rn(i[0],i[1]),p=v=>h.colors[yo[v]??"muted"],b=v=>h.colors[v==="verdict"?"good":v==="decision"?"accent":v==="question"?"warn":"muted"];return{style:vn(h),height:l,x:{range:i,log:!1,format:v=>Ln(v,w.step),label:"",splits:w.at},y:{range:[ze-.8,a+.5],log:!1,reverse:!0,label:"",size:150,splits:a<=40?[ze,...e.bars.map(v=>v.lane)]:[ze],format:v=>v===ze?"notes":To(e.bars[Math.round(v)]?.name??"")},draw:({ctx:v,x:H,y:K,px:V,focused:A})=>{let Y=Xt*.62*V;for(let D of e.bars){let P=H(D.start),S=Math.max(3*V,H(D.end)-P);v.fillStyle=A!==null&&A!==D.id?bn(p(D.status),.35):p(D.status),v.beginPath(),v.roundRect(P,K(D.lane)-Y/2,S,Y,3*V),v.fill()}for(let D of e.marks){let P=H(D.t),S=K(ze),ne=(A===D.id?6:4.5)*V;v.fillStyle=b(D.type),v.beginPath(),v.moveTo(P,S-ne),v.lineTo(P+ne,S),v.lineTo(P,S+ne),v.lineTo(P-ne,S),v.closePath(),v.fill()}},hit:(v,H,K,V)=>{if(Math.abs(H-V(ze))<Xt/2){let D=Eo(e.marks,P=>Math.abs(K(P.t)-v),8);return D?{key:D.id,rows:Co(D)}:null}let A=Math.round((H-V(0))/(V(1)-V(0))),Y=e.bars.find(D=>D.lane===A&&K(D.start)-3<=v&&v<=Math.max(K(D.end),K(D.start)+3)+3);return Y?{key:Y.id,rows:xo(Y)}:null},onClick:v=>{let H=e.marks.find(K=>K.id===v);H?R(E(H.group,{drawer:!0})):R(re(v))}}})(t):null,[i,e.bars,e.marks],t),d=h=>{if(!$.current)return;h.preventDefault();let w=$.current.xAt(h.clientX),p=Math.exp(h.deltaY*.0015);c(([b,v])=>Yt([w-(w-b)*p,w+(v-w)*p],o))},m=N(null),f=h=>m.current={x:h.clientX,range:i},g=h=>{if(!m.current||!$.current||!(h.buttons&1))return;let w=(h.clientX-m.current.x)*$.current.xPerPixel(),[p,b]=m.current.range;Math.abs(h.clientX-m.current.x)>3&&c(Yt([p-w,b-w],o))},C=Math.max(...s,Date.now()/1e3);return r`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${wo.map(([h,w])=>r`<button type="button" role="radio" aria-checked=${Math.abs(i[1]-i[0]-w)<1}
          onClick=${()=>c(Yt([C-w,C+w*.02],[Math.min(o[0],C-w),o[1]]))}>last ${h}</button>`)}
      <button type="button" role="radio" aria-checked=${i[0]===o[0]&&i[1]===o[1]} onClick=${()=>c(o)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${l}px`}
      onWheel=${d} onPointerDown=${f} onPointerMove=${g} onPointerUp=${()=>m.current=null}></div>
    <p class="muted small">${So(t)}</p>
  </div>`}function xo(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:W(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:Te(e.end-e.start),color:null}]}function Co(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:W(new Date(e.t*1e3).toISOString()),color:null}]}function So(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function Eo(e,t,n){let s=null,o=n;for(let i of e){let c=t(i);c<o&&([s,o]=[i,c])}return s}function cr(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function Yt([e,t],n){let s=Math.min(n[1]-n[0],Math.max(60,t-e)),o=Math.max(n[0],Math.min(e,n[1]-s));return[o,o+s]}function To(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function dr(){let e=M(Le),t=N(null);if(T(()=>{let o=t.current;if(!o||!e)return;o.showModal();let i=()=>Le.set(null);return o.addEventListener("close",i),()=>o.removeEventListener("close",i)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},s=String(n.props.title??n.props.y??"Chart");return r`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${s} closedby="any">
    <${F.Provider} value=${e.view}><${ue} node=${n} /><//>
  </dialog>`}function pr(e,t){let n=e.toLowerCase(),s=t.toLowerCase();if(!n)return 1;let o=s.indexOf(n);if(o>=0)return 100-Math.min(o,50)-s.length/100;let i=0,c=0;for(let a of s)if(a===n[i]?i++:i>0&&c++,i===n.length)return 40-Math.min(c,39);return 0}function $r(e){let[t,n]=y(e.query),[s,o]=y(0),i=N(null),c=L(k($e()).data),a=L(k(mt()).data);T(()=>{let p=i.current;p.showModal();let b=()=>te.set(null);p.addEventListener("close",b);let v=!1,H=A=>{let Y=p.getBoundingClientRect();return A.clientX<Y.left||A.clientX>Y.right||A.clientY<Y.top||A.clientY>Y.bottom},K=A=>v=H(A),V=A=>v&&H(A)&&p.close();return"closedBy"in HTMLDialogElement.prototype||(p.addEventListener("pointerdown",K),p.addEventListener("pointerup",V)),()=>{p.removeEventListener("close",b),p.removeEventListener("pointerdown",K),p.removeEventListener("pointerup",V)}},[]);let l=()=>i.current?.close(),u=p=>()=>R(p),$=U.value,d=$.page==="group"?$.path:".",m=(p,b,v,H)=>({section:"Commands",label:p,detail:b,sym:{icon:v,tone:"muted",label:p},run:H}),g=[...c.map(p=>({section:"Groups",label:p.path==="."?"local":p.path,detail:`${p.runs} runs${p.proposal?` \xB7 ${p.proposal}`:""}`,sym:_("research",p.status),run:u(E(p.path))})),...a.map(p=>({section:"Runs",label:p["run.name"]??p["run.id"],detail:`${p["run.status"]} \xB7 ${p["run.path"]}`,sym:_("run",p["run.status"]),run:u(E(p["run.path"]))})),m("Theme: light","","sun",()=>rt("light")),m("Theme: dark","","moon",()=>rt("dark")),m("Theme: follow the system","","monitor",()=>rt("system")),m("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),m("Show notes and timeline","i","file-text",u(E(d,{drawer:!0}))),m("Show or hide the sidebar","\u2318B","panel-left",()=>ee.set(!ee.value)),m(ae.value?"Resume live updates":"Pause live updates","p",ae.value?"play":"pause",()=>ae.set(!ae.value)),m("Keyboard shortcuts","?","keyboard",()=>ye.set(!0)),m("Settings","","settings",u("/settings/appearance"))].map(p=>({it:p,s:Math.max(pr(t,p.label),pr(t,p.detail)*.5)})).filter(p=>p.s>0).sort((p,b)=>b.s-p.s||mr(p.it.section)-mr(b.it.section)).slice(0,60).map(p=>p.it),C=p=>{p&&(l(),p.run())},h=p=>{if(p.key==="ArrowDown")o(Math.min(g.length-1,s+1));else if(p.key==="ArrowUp")o(Math.max(0,s-1));else if(p.key==="Enter")C(g[s]);else return;p.preventDefault()},w="";return r`<dialog class="sheet" ref=${i} aria-label="Search" closedby="any">
    <div class="palette-input"><${x} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${g[s]?`pal-${s}`:void 0}
        onInput=${p=>{n(p.target.value),o(0)}} onKeyDown=${h} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${g.map((p,b)=>{let v=p.section!==w&&!t?w=p.section:null;return r`${v?r`<li class="palette-head small" role="presentation">${v}</li>`:null}
          <li id=${`pal-${b}`} class="item" role="option" aria-selected=${b===s}
              onMouseMove=${()=>o(b)} onClick=${()=>C(p)}>
            <${O} spec=${p.sym} /><span class="label">${p.label}</span><span class="detail small">${p.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function mr(e){return["Groups","Runs","Commands"].indexOf(e)}function Ct(e,t=[]){let n=new Map,s=(a,l={})=>({path:a,name:a==="."?"local":a.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let a of e)n.set(a.path,s(a.path,a));(t.length===0||t.some(a=>a.name==="."))&&!n.has(".")&&n.set(".",s("."));for(let a of t){let l=a.name;n.has(l)||n.set(l,s(l)),Object.assign(n.get(l),{state:a.state,error:a.error})}for(let a of n.values()){if(q(a.path))continue;let l=a.path.lastIndexOf("/"),u=l<0?".":a.path.slice(0,l);(n.get(u)??n.get(Me(a.path))??n.get(".")).children.push(a)}for(let a of n.values())a.children.sort((l,u)=>l.name.localeCompare(u.name));let i=[...n.values()].filter(a=>a.path!=="."&&q(a.path)).sort((a,l)=>a.name.localeCompare(l.name)),c=n.get(".");return c?[c,...i]:i}function fr(e,t,n,s=new Set){let o=[],i=n.toLowerCase(),c=a=>{(!i||a.path.toLowerCase().includes(i)||hr(a,i))&&(o.push(a),(i||(q(a.path)?!s.has(a.path):t.has(a.path)))&&a.children.forEach(c))};return e.forEach(c),o}function hr(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||hr(n,t))}function gr(e,t){if(!t||q(t))return e;let n=t.split("/"),s=new Set(e);for(let o=t.startsWith("@")?2:1;o<n.length;o++)s.add(n.slice(0,o).join("/"));return s.size===e.size?e:s}function br(e,t){if(q(t))return e;let n=t.lastIndexOf("/"),s=n<0?".":t.slice(0,n),o=i=>i.path===s?i:i.children.map(o).find(c=>c)??null;return e.map(o).find(i=>i)?.children??[]}function vr(e){return q(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function yr(){let e=M(U),t=k($e()),[n,s]=y(()=>new Set(xe("open",[]))),[o,i]=y(()=>new Set(xe("closed-hosts",[]))),[c,a]=y(""),l=N(null),u=e.page==="group"?e.path:null,$=Ct(L(t.data),t.data?.meta?.sources??[]),d=fr($,n,c,o),m=h=>q(h)?!o.has(h):n.has(h),f=(h,w)=>{let p=w??!m(h);if(q(h)){let v=new Set(o);p?v.delete(h):v.add(h),he("closed-hosts",[...v]),i(v);return}let b=new Set(n);p?b.add(h):b.delete(h),he("open",[...b]),s(b)},g=N(u);return T(()=>{let h=gr(n,u);h!==n&&(he("open",[...h]),s(h)),u!==g.current&&u&&!q(u)&&o.has(Me(u))&&f(Me(u),!0),g.current=u},[u]),r`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${x} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${c} aria-label="Filter groups"
        onInput=${h=>a(h.target.value)} />
    </label>
    <div class="tree" ref=${l} onKeyDown=${h=>{let w=[...l.current?.querySelectorAll("a.tree-item")??[]],p=w.indexOf(document.activeElement),b=d[p];switch(h.key){case"ArrowDown":w[Math.min(w.length-1,p+1)]?.focus();break;case"ArrowUp":w[Math.max(0,p-1)]?.focus();break;case"ArrowRight":b?.children.length&&f(b.path,!0);break;case"ArrowLeft":b?.children.length&&m(b.path)?f(b.path,!1):b&&w[d.findIndex(v=>v.path===Do(b.path))]?.focus();break;default:return}h.preventDefault()}} role="tree">
      ${d.map(h=>r`<${Mo} key=${h.path} node=${h} current=${h.path===u}
        open=${m(h.path)||!!c} filtering=${!!c} onToggle=${()=>f(h.path)} />`)}
    </div>
  </nav>`}function Mo(e){let t=e.node,n=()=>Ye(t.path),s=t.children.length>0,o=t.state==="unreachable";return r`<a class=${`tree-item${e.current?" current":""}${q(t.path)?" source-root":""}`} href=${E(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${s?e.open:void 0}
      style=${`padding-inline-start:${8+vr(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${i=>{i.metaKey||i.ctrlKey||(i.preventDefault(),e.current&&s&&!e.filtering?e.onToggle():R(E(t.path)))}}>
    <span class=${`twisty${s?" expandable":""}`} aria-disabled=${s&&e.filtering?"true":void 0}
      onClick=${i=>{s&&(i.preventDefault(),i.stopPropagation(),e.filtering||e.onToggle())}}>
      ${s?r`<${x} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    ${q(t.path)?r`<${O} size=${14} spec=${{icon:o?"cloud-off":"server",tone:"muted",label:o?`Unreachable: ${t.error??"no answer"}`:t.path==="."?"This machine":`Remote host ${t.name}`}} />`:null}
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?r`<${O} spec=${_("run","running")} size=${14} />`:null}
      ${t.failed?r`<${O} spec=${{..._("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function Do(e){if(q(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function kr(){let e=M(U),t=M(ee),n=M(te),s=M(ye),o=N(null);T(()=>mn(()=>o.current),[]),T(()=>(addEventListener("keydown",wr),()=>removeEventListener("keydown",wr)),[]);let i=e.page==="group"&&e.drawer,c;switch(e.page){case"group":c=r`<${ar} key=${`${e.path} ${e.version} ${e.draft} ${e.history} ${e.hiddenRuns}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} hiddenRuns=${e.hiddenRuns} />`;break;case"run":c=r`<${lr} id=${e.id} />`;break;case"settings":c=r`<${ps} />`;break;case"timeline":c=r`<${ur} key=${e.from} from=${e.from} />`;break;default:c=r`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return le||!1?r`<main class="main render-main" ref=${o}>${c}</main>`:r`<div class=${`shell${t?"":" no-sidebar"}${i?" with-drawer":""}`}>
    <${$s} />
    ${t?r`<${yr} />`:null}
    <main class="main" ref=${o}>${c}</main>
    ${i?r`<${Es} path=${e.path} run=${e.run} />`:null}
    <${fs} />
    ${n!==null?r`<${$r} query=${n} />`:null}
    ${s?r`<${No} />`:null}
    <${dr} />
  </div>`}function wr(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),te.set(te.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),ee.set(!ee.value);return}if(e.key==="Escape"){if(te.value!==null||ye.value)return;let s=U.value;return s.page==="group"&&s.run?R(E(s.path,{drawer:!0}),{replace:!0}):s.page==="group"&&s.drawer?R(E(s.path),{replace:!0}):void 0}if(t||e.altKey||us(e)||te.value!==null||ye.value)return;let n=U.value;switch(e.key){case"/":e.preventDefault(),te.set("");break;case"?":ye.set(!ye.value);break;case"p":ae.set(!ae.value);break;case"i":n.page==="group"&&R(E(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":ee.set(!ee.value);break;case"[":case"]":n.page==="group"&&Po(n.path,e.key==="]"?1:-1);break}}async function Po(e,t){let n=await Ne($e()),s=br(Ct(L(n),n?.meta?.sources??[]),e),o=s.findIndex(c=>c.path===e),i=s[o+t];i&&R(E(i.path))}function No(){let e=N(null);return T(()=>{let t=e.current;t.showModal();let n=()=>ye.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),r`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${ht.map(([t,n])=>r`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${Q} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}fn();if(le){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(ge.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Ke.n,hn&&xn()}jn();var Ro=j("meta").then(e=>(le&&(e={...e,settings:{...e.settings,theme_mode:ge.value}}),gt(e),e));!le&&!!1&&pn(async()=>{let[e,t]=await Promise.all([Ro,j("meta")]);e.bundle!==t.bundle?location.reload():gt(t)});Jt(r`<${kr} />`,document.getElementById("app"));
