import{$ as ot,$a as Vn,A as mn,Aa as En,B as Re,Ba as qe,C as ie,Ca as ct,D as E,Da as Pt,E as nt,F as re,Fa as Tn,G as de,H as Me,Ha as Dt,I as X,Ia as Mn,J as F,K as $n,La as Pn,M as D,Ma as Dn,N as fn,Na as Nn,O as hn,Oa as In,P as he,Pa as On,Q as Le,Qa as zn,R as gn,Ra as Bn,S as st,T as Pe,Ta as An,U as ge,V as wn,Va as Hn,W as Tt,Wa as Kn,X as rt,Xa as Un,Y as W,Ya as Fn,Z as J,Za as Wn,_ as pe,_a as jn,a as r,aa as kn,b as nn,c as He,ca as _e,d as se,da as be,e as tt,fa as xn,ga as Cn,h as sn,ha as x,i as rn,ia as O,j as Ke,ja as at,k as on,ka as oe,l as an,la as z,m as ln,ma as N,na as We,oa as I,pa as Ce,q as G,qa as B,r as Ue,ra as Q,s as Ne,sa as je,t as Et,ta as Ve,u as w,ua as it,v as cn,va as lt,w as ae,wa as R,x as un,xa as Ge,y as dn,ya as Mt,z as pn,za as Sn}from"./chunks/chunk-WCHCQV4U.js";import{a as tn,b as Qe}from"./chunks/chunk-O2K4N3UR.js";import{$ as _n,C as $e,D as M,E as xe,F as fe,K as bn,M as Fe,Q as vn,R as yn,V as Rn,_ as Ln,b as Jt,d as Qt,f as y,g as T,h as en,i as P,j as Ee,k as Z,q,r as St,t as ke,u as ue,v as Te,w as et,x as V,y as Ae}from"./chunks/chunk-OMABMV2V.js";import"./chunks/chunk-VC46IEJQ.js";function De(e,t){Re(n=>t.includes(n.method)&&n.scope!==null&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var Nt=["notes","timeline","groups","check","card","memory_show","status"];async function ut(e,t){let n=e.meta??{};await G("note_add",{group:e.group,type:t.type??e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),De(e.group,Nt)}async function Gn(e,t,n,s){await G("note_add",{group:e,type:t,description:n,body:s}),De(e,Nt)}async function qn(e,t){await G("memory_update",{group:e,body:t}),De(e,["memory_show","status"])}async function Xn(e,t){let n=await G("proposal_show",{group:e}),s=Object.fromEntries(Object.entries(n.proposal??{}).filter(([o])=>!["schema","author","user","supersedes"].includes(o)));await G("proposal_set",{group:e,proposal:{...s,statement:t}}),De(e,["groups","proposal_show","check","summary"])}async function Yn(e){await G("note_rm",{note:e.id}),De(e.group,Nt)}async function Zn(e,t,n){await G("name",{run:e,name:n}),De(t,["card","runs","groups","summary","series"])}async function Rt(e,t){await G("run_promote",{runs:[de(e,t)]}),De(t,["card","runs","groups","summary","series","keys","check","proposal_show","status"])}async function dt(e,t,n){let s=await G("view_text",{path:e,id:t,text:n});return Re(o=>["view","view_history"].includes(o.method)&&o.scope===e),s.id}async function Jn(e){await G("view_upgrade",{group:e}),Re(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var Ie=new $e(null);async function Qn(e,t){return await G("set",{key:e,value:t}),G("meta")}var me=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),ve=(e,t=null,n=null,s=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{},...s?{metrics:s}:{}},scope:e}),Lt=(e,t=null)=>({method:"summary",params:{path:e,...t?{metrics:t}:{}},scope:e}),Oe=e=>({method:"groups",params:{from:e,depth:0},scope:e}),es=e=>({method:"check",params:{group:e},scope:e}),ts=e=>({method:"proposal_show",params:{group:e},scope:e}),ze=(e,t)=>({method:"card",params:{run:de(e,t)},scope:t}),ns=(e,t)=>({method:"output",params:{run:de(e,t),tail:30},scope:t}),ss=(e,t)=>({method:"run_diff",params:{run:de(e,t)},scope:t}),Xe=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),rs=e=>({method:"runs",params:{from:e,hidden:!0,where:{"run.hidden":!0},select:["run.name","run.status","run.created_at"],limit:200},scope:e}),pt=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),os=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),as=()=>({method:"status",params:{},scope:"."}),mt=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function Ye(e){let t=He(e).value.main;for(let n of[ve(e,null,null,t),Oe(e),Xe(e),Lt(e,t)])Et(n);Ne(ve(e,null,null,t)).then(n=>{for(let s of is(n.view))Et(s)}).catch(()=>{})}function is(e){return e?[...kr.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(is)]:[]}var kr=new Set(["line","custom"]),ls=e=>({method:"view_history",params:{group:e},scope:e});var ft="/static/favicon.svg",$t=null;async function xr(){if($t)return $t;let e=new Image;e.src=ft,await e.decode();let t=32,n=document.createElement("canvas");n.width=n.height=t;let s=n.getContext("2d");if(!s)return ft;let o=getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();return o?(s.drawImage(e,0,0,t,t),s.beginPath(),s.arc(t-6,t-6,6,0,Math.PI*2),s.fillStyle=o,s.fill(),$t=n.toDataURL("image/png"),$t):ft}function Cr(e){if(!1)return;let t=document.querySelector("link[rel=icon]");if(t instanceof HTMLLinkElement){if(!e){t.type="image/svg+xml",t.href=ft;return}xr().then(n=>{t.type="image/png",t.href=n})}}function Ze(e,t=0){T(()=>{document.title=`${t?`(${t}) `:""}${e} \xB7 Beamtime`,Cr(t>0)},[e,t])}function cs(e){let t=ie(e.split("/").pop()??""),n=w(t?null:Oe(e)),s=w(t?ze(e.split("/").pop()??"",e):null),o=t?s.data?.run.name??s.data?.run.id??e:e==="."?"local":e.split("/").pop()??e,i=t?s.data?.run.status==="running"?1:0:N(n.data)[0]?.running??0;Ze(o,i)}var ee=new $e(xe("sidebar",!0)),te=new $e(null),ye=new $e(!1),we=new $e(null);ee.subscribe(e=>fe("sidebar",e));var us=xe("visit",Date.now());fe("visit",Date.now());function ds(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var ht=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var Sr=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function gt(e){we.set(e),pn(e.stale),st.set(e.theme),Fe.set(e.colormaps),e.settings?.theme_mode&&ge.set(e.settings.theme_mode),Tt()}var ps=0;async function _t(e,t){let n=++ps;e==="theme_mode"&&(ge.set(t),Tt());let s=await Qn(e,t);n===ps&&gt(s)}function ms(){let e=M(ge),t=pe(),n=M(we),[s,o]=y(null);Ze("Settings");let i=(c,u)=>{o(null),_t(c,u).catch($=>o($.message))},l=n?.settings??{},a=(c,u,$)=>r`
    <label class="field-label small" for=${`setting-${c}`}>${u}</label>
    <span class="input body">
      <select id=${`setting-${c}`} value=${l[c]} onChange=${d=>i(c,d.target.value)}>
        ${$.map(d=>r`<option value=${d}>${d}</option>`)}
      </select>
    </span>`;return r`<div class="page settings"><div class="sections">
    <${B} label="settings">
      <h1 class="page-title title" tabindex="-1">Settings</h1>
      <p class="muted small">Changes are written to <code>${l.file??"beamtime.yaml"}</code>, the project's settings.</p>
      ${s?r`<${z} kind="error">${s}<//>`:null}
    <//>
    <${B} label="appearance">
      <div class="settings-rows">
        <span class="field-label small">Mode</span>
        <div class="segmented" role="radiogroup" aria-label="Theme mode">
          ${Sr.map(([c,u,$])=>r`<button type="button" role="radio" aria-checked=${e===c} onClick=${()=>i("theme_mode",c)}>
            <${x} name=${u} size=${15} />${$}</button>`)}
        </div>
        ${a("theme","Theme",n?.themes??[])}
      </div>
      <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files recolor this layout: they go in <code>themes/</code> next to
        beamtime.yaml. Colormaps are chosen in each chart's settings.</p>
      ${(n?.theme?.problems??[]).map(c=>r`<${z} kind="warning">${c}<//>`)}
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
      <table class="kv">${ht.map(([c,u])=>r`<tr><td><kbd class="small">${c}</kbd></td><td>${u}</td></tr>`)}</table>
    <//>
    <${B} label="about">
      <table class="kv">
        <tr><td class="muted">version</td><td>${n?.version}</td></tr>
        <tr><td class="muted">root</td><td><code class="code">${n?.root}</code></td></tr>
        ${(n?.sources??[]).map(c=>r`
          <tr><td class="muted">${c.name==="."?"local":c.name}</td><td><code class="code">${c.logdir}</code> (${c.kind}, ${c.state})</td></tr>`)}
      </table>
    <//>
  </div></div>`}var $s={system:"light",light:"dark",dark:"system"},Er={system:"monitor",light:"sun",dark:"moon"};function fs(){let e=M(we),t=M(ge),n=M(ee);return r`<header class="topbar">
    <${I} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>ee.set(!n)} />
    <a class="project heading" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>te.set("")} aria-label="Search (⌘K)">
      <${x} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${Tr} />
      <${I} icon=${Er[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${$s[t]})`}
        onClick=${()=>{_t("theme_mode",$s[t])}} />
      <a class="icon-button" href=${nt(F.value.page==="group"?F.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${x} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${x} name="settings" size=${16} /></a>
    </div>
  </header>`}function Tr(){let t=(w(me()).data?.meta?.sources??[]).filter(n=>n.name!==".");return t.length?r`${[{name:".",state:"connected"},...t].map(n=>r`<a class=${`source small ${n.state}`}
      href=${E(n.name)}
      data-tip=${n.state==="connected"?`${n.name==="."?"local":n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${x} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name==="."?"local":n.name}</a>`)}`:r`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${x} name="server" size=${15} /> local</span>`}function Mr(e){let[t,n]=y(Date.now());return T(()=>{let s=setInterval(()=>n(Date.now()),e);return()=>clearInterval(s)},[e]),t}function Pr(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function hs(){let e=M(un),t=M(ae),n=M(dn),s=M(F),o=Mr(5e3),i=w(as()).data,l=N(w(mt()).data),a=M(we),c=i?.daemon,u=i?.runs?.running??0,$=l.filter(C=>C["run.status"]==="failed"&&Pr(C["run.ended_at"])>us).length,d=i?.meta?.freshness,[m,f,h]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&c?["",`live \xB7 updated ${V(new Date(n).toISOString(),o)}`,`beamtime serve, pid ${c.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return r`<footer class="statusbar small">
    <span class="status-item" data-tip=${h}><span class=${`live-dot ${m}`}></span>${f}</span>
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
  </footer>`}var gs=null;function bt(e){let t=P(null),[n,s]=y(null),[o,i]=y(!1),[l,a]=y(!1);T(()=>{let d=!0;return gs??=import("./chunks/md-SW3VT2BQ.js"),gs.then(m=>m.render(e.text??"")).then(m=>d&&s(m)),()=>{d=!1}},[e.text]),en(()=>{let d=t.current;if(!d||!e.clamp)return;let m=()=>a(d.scrollHeight>d.clientHeight+2),f=new ResizeObserver(m);return f.observe(d),()=>f.disconnect()},[e.clamp,n]);let c=e.clamp&&!o,u=`md${c?" clamped":""}`,$=c?`--clamp:${e.clamp}`:"";return r`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?r`<div class=${u} ref=${t} style=${$}>
          ${(e.text??"").split(/\n{2,}/).map(d=>r`<p>${d}</p>`)}
        </div>`:r`<div class=${u} ref=${t} style=${$} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(l||o)?r`<button type="button" class="link small more" onClick=${()=>i(!o)}>${o?"less":"more"}</button>`:null}
  </div>`}function Se(e){let[t,n]=y(!!e.startEditing),[s,o]=y(e.value),[i,l]=y(null),[a,c]=y(null),u=P(null),$=P(!1);T(()=>l(null),[e.value]),T(()=>{!t||!u.current||(u.current.focus(),e.startEditing?u.current.select():u.current.setSelectionRange(u.current.value.length,u.current.value.length))},[t]);let[d,m]=y(!1),f=e.locked??void 0,h=b=>{if(!b.target.closest("a, button, input, summary")){if(f)return m(!0);b.preventDefault(),o(i??e.value),c(null),$.current=!1,n(!0)}},C=()=>{$.current=!0,n(!1),c(null),e.onCancel?.()},g=async()=>{if($.current)return;$.current=!0;let b=e.multiline?s.trim():s.replace(/\s*\n\s*/g," ").trim();if(b===e.value.trim()||!b&&!e.multiline)return C();n(!1),l(b);try{await e.onSave(b)}catch(v){l(null),o(b),c(v.message),$.current=!1,n(!0)}},k=b=>{if(b.key==="Escape")return b.preventDefault(),b.stopPropagation(),C();b.key!=="Enter"||b.isComposing||b.keyCode===229||(!e.multiline||b.metaKey||b.ctrlKey)&&(b.preventDefault(),g())};if(t)return r`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${u} class="edit-field" value=${s} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,s.split(`
`).length+1)):1}
        onInput=${b=>o(b.target.value)} onKeyDown=${k} onBlur=${g}></textarea>
      <span class="edit-hint small">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${a?r` · <span class="bad-text">${a}</span>`:null}</span>
    </div>`;let p=i??e.value;return r`<div class=${`editable${f?" locked":""}${i!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${f?`${e.label}: ${f}`:`Edit ${e.label}`}
      data-tip=${f} onClick=${h} onBlur=${()=>m(!1)}
      onKeyDown=${b=>b.key==="Enter"&&b.target===b.currentTarget&&h(b)}>
    ${p.trim()?e.render?e.render(p):p:r`<span class="muted">${e.placeholder??"Click to write"}</span>`}
    ${d&&f?r`<span class="edit-hint small locked-why" role="status"><${x} name="lock" size=${14} /> ${f}</span>`:null}
  </div>`}function It(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function bs({node:e}){let t=J("proposal"),n=J("check"),s=t.data,o=n.data;if(!s)return r`<${oe} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let i=s.proposal??{},l=(s.versions??[]).filter(c=>c.version!==s.version),a=!e.props.of||e.props.of===".";return r`<${oe} title="Predictions" result=${t} class="proposal">
    ${a?null:r`<p class="statement">${i.statement}</p>`}
    ${i.rationale?r`<p class="rationale prose">${i.rationale}</p>`:null}
    <${En} predictions=${o?.predictions} />
    ${l.length?r`<${Ve} summary=${`${l.length} earlier version${l.length>1?"s":""}`}>
          ${l.map(c=>r`<p class="small"><code>${c.version}</code> ${c.statement}
            <span class="muted">(${c.runs} runs, check ${c.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function vs({node:e}){let t=J("main"),n=e.data?.main.params.group??".",s=t.data?.chain??[],o=s.find(a=>a.group===n)??null,i=s.filter(a=>a.group!==n),l=o?.notes_since?"out of date":o?`version ${o.versions??1}`:"none yet";return r`<${We} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?l:void 0} open=${!1} result=${t}
      action=${r`<${O} spec=${{icon:"circle-help",tone:"muted",label:Nr}} />`}>
    <${Se} value=${o?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${a=>r`<${bt} text=${a} />`} onSave=${a=>qn(n,a)} />
    ${o&&(o.body?.length>(t.data?.budget??1/0)||o.notes_since>=Dr)?r`<p class="memory-meta small warn-text">${o.body?.length>t.data.budget?`${o.body.length} characters, beyond the budget of ${t.data.budget}`:`${o.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${o?r`<p class="memory-meta small">${o.author} · covers notes until ${o.covers_until?.slice(0,10)}
          ${o.notes_since?r` · <span class="warn-text">${o.notes_since} newer note${o.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${i.length?r`<p class="memory-meta small">Memory above this group: ${i.map((a,c)=>r`${c?", ":""}<a href=${E(a.group)}>${a.group==="."?"local":a.group}</a>`)}</p>`:null}
  <//>`}var Dr=5,Nr="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",Rr="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function ys({node:e}){let t=J("main"),n=e.data?.main.params.from??".",s=N(t.data).filter(o=>o.path!==n);return r`<${oe} title=${e.props.title} count=${t.data?String(s.length):void 0} result=${t}>
    ${t.data&&!s.length?r`<${z}>No groups below.<//>`:null}
    <div class="group-list">
      ${s.map(o=>{let[i,l]=It(o.progress),a=(o.failed??0)+(o.killed??0)+(o.lost??0);return r`<a class="group-row" key=${o.path} href=${E(o.path)}
            onPointerEnter=${()=>Ye(o.path)} onFocus=${()=>Ye(o.path)}>
          <${O} spec=${R("research",o.status)} />
          <span class="gname heading">${o.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${o.status!=="concluded"?r`<span class=${`tone-${R("research",o.status).tone}`}>${R("research",o.status).label}</span>`:null}
            ${o.check?r`<${O} spec=${R("result",o.check)} word />`:null}
            ${o.verdict?r`<${O} spec=${R("verdict",o.verdict)} />`:null}
            ${i?r`<span data-tip=${l}>${i}</span>`:null}
            <span class="num"><b>${o.runs}</b> runs</span>
            ${o.running?r`<${O} spec=${R("run","running")} />`:null}
            ${a?r`<span class="tone-bad num" data-tip="failed, killed or lost"><${x} name="circle-x" size=${14} /> ${a}</span>`:null}
          </span>
          ${o.proposal?r`<span class="gstatement caption">${o.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function ws({node:e}){let t=J("main"),n=e.data?.main.params.from??".",[s,o]=y(!1),i=(t.data?.entries??[]).filter(a=>!String(a.state??"").startsWith("superseded")),l=t.data?.meta?.matched??i.length;return r`<${We} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(l):void 0} result=${t}
      action=${r`<${O} spec=${{icon:"circle-help",tone:"muted",label:Rr}} />
        ${r`<${I} icon="plus" label="Add a note" onClick=${()=>o(!0)} />`}`}>
    <div class="notes">
      ${s?r`<${Ir} group=${n} onDone=${()=>o(!1)} />`:null}
      ${t.data&&!i.length&&!s?r`<p class="muted small">No notes yet.</p>`:null}
      ${i.map(a=>r`<${vt} key=${a.id} note=${a} scope=${n} />`)}
      ${t.data?.more&&e.data?r`<${ks} call=${e.data.main} before=${i[i.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var Lr=20;function ks(e){let[t,n]=y(!1),s=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:Lr}}:null,o=w(s);if(!t)return r`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(o.status==="error")return r`<p class="bad-text small">${o.error}</p>`;let i=o.data?.entries??[];return r`${o.data?null:r`<div class="skeleton" style="block-size: 40px"></div>`}
    ${i.map(l=>r`<${vt} key=${l.id} note=${l} scope=${e.scope} />`)}
    ${o.data?.more?r`<${ks} call=${e.call} before=${i[i.length-1]?.id} scope=${e.scope} />`:null}`}var _r=["observation","decision","idea","question","theory"];function xs(e){return(e?.note_types??_r).filter(t=>t!=="verdict")}function Ir(e){let t=xs(M(we)),[n,s]=y("observation"),[o,i]=y(""),[l,a]=y(""),[c,u]=y(null),[$,d]=y(!1),m=async h=>{if(h.preventDefault(),!o.trim())return u("give the note a title");d(!0);try{await Gn(e.group,n,o.trim(),l.trim()),e.onDone()}catch(C){u(C.message),d(!1)}};return r`<form class="note new-note" onSubmit=${m} onKeyDown=${h=>{h.key==="Escape"&&e.onDone(),h.key==="Enter"&&(h.metaKey||h.ctrlKey)&&m(h)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${n} aria-label="Note type" onChange=${h=>s(h.target.value)}>
        ${t.map(h=>r`<option value=${h}>${h}</option>`)}
      </select></span>
      <span class="input body new-note-field"><input class="new-note-title" value=${o} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${h=>i(h.target.value)} /></span>
    </div>
    <span class="input small"><textarea class="new-note-body" rows="4" value=${l} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${h=>a(h.target.value)}></textarea></span>
    <div class="save-actions">
      <${Q} type="submit" icon=${$?"hourglass":"plus"} disabled=${$}>${$?"Adding\u2026":"Add note"}<//>
      <${Q} icon="x" kind="quiet" onClick=${e.onDone}>Cancel<//>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${c?r`<span class="bad-text small">${c}</span>`:null}
    </div>
  </form>`}function Or({note:e}){let t=xs(M(we)).filter(n=>n!==e.type);return e.type==="verdict"?r`<span class="sym tone-accent" data-tip="a verdict's type can't change; write a new note">
      <${x} name=${R("note","verdict").icon} size=${15} /></span>`:r`<${it} icon=${R("note",e.type).icon} label="Change the note's type" title="Note type">
    <div class="menu-list">
      ${t.map(n=>r`<button type="button" key=${n} onClick=${()=>ut(e,{type:n})}>
        <${x} name=${R("note",n).icon} size=${15} /> ${n}</button>`)}
    </div>
  <//>`}function vt(e){let t=e.note,[n,s]=y(!!e.open),[o,i]=y(!1),l=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,a=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),c=t.meta?.author;return r`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${u=>!u.target.closest(".editable, a, .note-delete, .popover-wrap")&&s(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${x} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${Or} note=${t} />
      <${Se} value=${t.description} label="the note's title" class="note-title prose" render=${Br}
        onSave=${u=>ut(t,{description:u})} />
      ${t.overall?r`<${O} spec=${R("verdict",t.overall)} />`:null}
      ${t.state?r`<${Ce} tone="warn">${t.state}<//>`:null}
      ${l?r`<a class="note-group small" href=${E(l)} data-tip="from this group">${zr(l,e.scope)}</a>`:null}
      <span class="note-meta small">${c?`${c} \xB7 `:""}${V(a)}</span>
      ${r`<${I} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${o}
        onClick=${u=>{u.stopPropagation(),i(!o)}} />`}
    </div>
    ${o?r`<div class="note-confirm small" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <${Q} icon="trash" kind="danger" onClick=${()=>{Yn(t)}}>Delete<//>
          <${Q} icon="x" kind="quiet" onClick=${()=>i(!1)}>Cancel<//>
        </div>`:null}
    ${n?r`<${Se} value=${t.body??""} label="the note" multiline class="note-body prose markdown"
          placeholder="Add details in Markdown" render=${u=>r`<${bt} text=${u} />`}
          onSave=${u=>ut(t,{body:u})} />`:null}
  </article>`}function zr(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,s=n.split("/").pop()??n;return ie(s)?s.slice(-8):n}function Cs({node:e}){let t=J("main"),n=t.data?.lines??[],s=t.data?.meta??{},o=r`<${x} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${s.total_lines??n.length} lines${(s.shown??0)<(s.total_lines??0)?`, last ${s.shown}`:""}`:""}</span>`;return r`<${oe} result=${t}>
    <${Ve} summary=${o} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function Ss({node:e}){let t=Z(W);return r`<${oe} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${Se} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${Ie.value===e.id} onCancel=${()=>Ie.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>r`<${bt} text=${n} />`}
      onSave=${n=>(Ie.set(null),dt(t.path,e.id,n))} />
  <//>`}function Es({node:e}){return r`<${z} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function Br(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let s=n.slice(2,-2),[o]=s.split(/[#@]/),i=o.split("/").pop()??"";return r`<a href=${ie(i)?re(i):E(o)}>${s}</a>`}return n.startsWith("`")?r`<code>${n.slice(1,-1)}</code>`:n})}function Ar(e,t){let n=/^(?:ssh|https?|git):\/\/(?:[^@/]*@)?([^/:]+)(?::\d+)?\/(.+?)(?:\.git)?\/?$/.exec(e??""),s=/^(?:[^@/]+@)?([^/:]+):(?!\/)(.+?)(?:\.git)?\/?$/.exec(e??""),[,o,i]=n??s??[];return!o||!i?null:o==="github.com"?{host:"GitHub",url:`https://github.com/${i}/commit/${t}`}:o==="gitlab.com"||o.startsWith("gitlab.")?{host:"GitLab",url:`https://${o}/${i}/-/commit/${t}`}:null}function yt(e){let{git:t,copied_from:n}=e.run,s=[];return t?.commit&&s.push(["code",r`<${Hr} git=${t} />`]),n&&s.push(["copied from",r`<a href=${re(n.id)} data-tip=${`${n.id}, ${n.at}`}>${n.path??n.id}</a>`]),e.checkpoints?.length&&s.push(["checkpoints",r`${e.checkpoints.map(o=>r`<${Kr} key=${o.name} ck=${o} />`)}`]),s}function Hr({git:e}){let t=Ar(e.remote,e.commit);return r`<span>${e.commit.slice(0,10)}${e.branch?r` on ${e.branch}`:null}
    ${e.dirty?r` <${Ce} tone="warn" tip="Uncommitted changes when the run started">dirty<//>`:null}
    ${t?r` · <a href=${t.url} target="_blank" rel="noopener noreferrer">${t.host}</a>`:null}</span>`}function Kr({ck:e}){let t=()=>{navigator.clipboard?.writeText(e.location)};return r`<div class="checkpoint">
    <span class=${e.exists?"":"muted"} data-tip=${e.location??void 0}>${e.name}</span>
    ${e.exists?null:r`<${Ce} tone="warn" tip=${e.location??void 0}>missing<//> <span class="muted">${Ur(e)}</span>`}
    ${e.location?r`<${I} icon="copy" label=${`Copy the path of ${e.name}`} onClick=${t} />`:null}
  </div>`}function Ur(e){return e.location?e.via==="origin"?"not found where the source run kept it":"not found at its recorded location":"no location recorded"}function wt({run:e,scope:t}){let[n,s]=y(!1),o=w(n?ss(e,t):null);return r`<${Ve} summary="Uncommitted changes" onToggle=${s}>
    ${o.error?r`<p class="muted small">${o.error}</p>`:null}
    ${o.data?r`<pre class="log code diff">${String(o.data.text).split(`
`).map(i=>r`<span class=${Fr(i)}>${i}\n</span>`)}</pre>`:n&&!o.error?r`<div class="skeleton late" style="block-size: 80px"></div>`:null}
  <//>`}function Fr(e){return e.startsWith("+++")||e.startsWith("---")||e.startsWith("@@")?"muted":e.startsWith("+")?"tone-good":e.startsWith("-")?"tone-bad":""}function Ts(e){let t=()=>D(E(e.path),{replace:!0});return r`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${x} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${I} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?r`<${Wr} id=${e.run} scope=${e.path} />`:r`<${jr} path=${e.path} />`}
  </aside>`}function Wr({id:e,scope:t}){let n=w(ze(e,t)).data,s=w(ns(e,t)).data,o=w(Xe(t)).data,i=w({method:"keys",params:{from:t},scope:t}).data,l=pe(),a=Ee(()=>ot(N(o).map(m=>m["run.id"]),l).get(e),[o,l,e]);if(!n)return r`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let c=n.run,u=Object.entries(n.metrics??{}),$=bn(a,l),d=yt(n);return r`<div class="drawer-body">
    <h3 class="heading"><span class=${$.class} style=${$.style}></span>
      <a href=${re(e)}>${c.name}</a></h3>
    <p class="facts small">
      <${O} spec=${Ge(c.status,c.exit)} word tip=${et(c)} />
      <span><b>${ue(c.steps)}</b> steps</span>
      <span><b>${Te(c.duration_s)}</b></span>
      <span data-tip=${c.created_at}>${V(c.created_at)}</span>
    </p>
    ${c.error?r`<pre class="log code bad-text">${c.error}</pre>`:null}
    ${d.length?r`<table class="kv small">${d.map(([m,f])=>r`<tr><td class="muted">${m}</td><td>${f}</td></tr>`)}</table>`:null}
    ${c.git?.dirty?r`<${wt} run=${c.id} scope=${t} />`:null}
    <h4 class="small">Config</h4>
    <${ct} config=${n.config??{}} varying=${qe(i)} />
    ${u.length?r`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${u.map(([m,f])=>r`<tr><td>${m}</td><td class="num"><b>${q(f.last)}</b></td>
              <td class="num">${q(f.min)}</td><td class="num">${q(f.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?r`<h4 class="small">Cited by</h4>${n.cited_by.map(m=>r`<p class="small"><${O} spec=${R("note",m.type)} /> ${m.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(m=>r`<div class="event small"><span class="muted num">${m.t?.slice(5,16).replace("T"," ")}</span>
        <${x} name=${Mt(m.type)} size=${14} /><span>${m.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(s?.lines??[]).join(`
`)}</pre>
  </div>`}function jr({path:e}){let t=w(pt(e)).data,n=w(os(e)).data;return r`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?r`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(s=>!String(s.state??"").startsWith("superseded")).map(s=>r`<${vt} key=${s.id} note=${s} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(s=>r`<div class="event small"><span class="muted num">${s.t?.slice(5,16).replace("T"," ")}</span>
        <${x} name=${s.kind==="note"?"file-text":Mt(s.type)} size=${14} />
        <span>${s.run?r`<a href=${re(s.run)}>${s.run.slice(-8)}</a> `:null}${s.description??s.type}</span></div>`)}
  </div>`}function kt(e,t){let n=w(e),s=P(null);return n.status!=="loading"&&(s.current={scope:t,result:n}),n.status==="loading"&&s.current?.scope===t?s.current.result:n}var Ot=null;function Ms(e){Ot?.();let t=document.querySelector(".main");if(!e||!t)return;let n=e.getBoundingClientRect().top,s=new ResizeObserver(()=>{e.isConnected&&(t.scrollTop+=e.getBoundingClientRect().top-n)});for(let a of t.children)s.observe(a);let o=["wheel","touchmove","keydown","pointerdown"],i=()=>{s.disconnect(),clearTimeout(l);for(let a of o)removeEventListener(a,i);Ot=null},l=setTimeout(i,5e3);for(let a of o)addEventListener(a,i,{passive:!0});Ot=i}var zt=["failed","killed","lost"],Vr={icon:"eye-off",tone:"muted",label:"Hidden"},Gr="Hidden: left out of tables, counts and checks until promoted";function Bt(e){let t=Me(e.path),n=t==="."?e.path:e.path.slice(t.length+1),s=X(e.path)?[]:n.split("/"),o=s.length&&ie(s[s.length-1])?s[s.length-1]:null,i=s.slice(0,-1),l=a=>[...t==="."?[]:[t],...i.slice(0,a+1)].join("/");return r`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${s.length?r`<a href=${E(t)}>${t==="."?"local":t}</a>`:null}
      ${i.map((a,c)=>r`<span>/</span><a href=${E(l(c))}>${a}</a>`)}
    </nav>
    ${o?r`<${Yr} id=${o} scope=${e.path} />`:r`<${qr} path=${e.path} />`}
    ${e.finding?r`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function qr({path:e}){let t=N(w(Oe(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return r`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let s=M(F),o=s.page==="group"&&s.hiddenRuns,i=Object.entries(w({method:"keys",params:{from:e},scope:e}).data?.codes??{}),l=zt.reduce((a,c)=>a+(t[c]??0),0);return r`
    <h1 class="page-title title" tabindex="-1">${n} <${O} spec=${R("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?r`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?r`<span><b>${t.finished}</b> finished</span>`:null}
      ${l?r`<span class="tone-bad" data-tip=${zt.filter(a=>t[a]).map(a=>`${t[a]} ${a}`).join(", ")}>
            <${x} name="circle-x" size=${15} /> <b>${l}</b> ${l===1?zt.find(a=>t[a]):"ended early"}</span>`:null}
      ${i.length?r`<span data-tip=${i.map(([a,c])=>`${a}: ${c} run${c===1?"":"s"}`).join(", ")}>
            <${x} name="git-commit" size=${15} /> <b>${i.length}</b> code versions</span>`:null}
      ${t.hidden?r`<span><a href=${E(e,{hidden:!o})} data-tip=${o?"Close the list of hidden runs":"List the hidden runs"}>
            <${x} name="eye-off" size=${15} /> <b>${t.hidden}</b> hidden</a></span>`:null}
      ${t.notes?r`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${Ns} path=${e} />
    </p>`}function Ps({path:e}){let t=N(w(rs(e)).data);return t.length?r`<${B} label="hidden runs">
    <table class="runs">
      <thead><tr class="small"><th>run</th><th>status</th><th>created</th><th></th></tr></thead>
      <tbody>${t.map(n=>r`<tr key=${n["run.id"]}>
        <td><a href=${re(n["run.id"],e)}>${n["run.name"]??n["run.id"]}</a></td>
        <td><${O} spec=${Ge(n["run.status"],null)} word /></td>
        <td class="muted" data-tip=${n["run.created_at"]}>${V(n["run.created_at"])}</td>
        <td><${Q} icon="eye" kind="quiet" onClick=${()=>Rt(n["run.id"],e)}>Promote<//></td>
      </tr>`)}</tbody>
    </table>
  <//>`:null}function Ds({path:e}){let t=N(w(Oe(e)).data)[0]??null,n=w(t?.proposal?es(e):null).data,s=w(t?.proposal?ts(e):null).data;if(!t?.proposal)return null;let o=s?.proposal?.rationale,i=s?.versions?.find(c=>c.version===s.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[l,a]=It(n?.progress?.text??t.progress);return r`<${B} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${Se} value=${t.proposal} label="the proposal's statement" locked=${s?i:"Loading the proposal\u2026"}
          render=${c=>r`<span data-tip=${i?void 0:o}>${c}</span>`}
          onSave=${c=>Xn(e,c)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(c=>{let u=R("result",c.result),$=Sn(c),d=$?`${u.label}: ${$}`:u.label;return r`<span class=${`check small tone-${u.tone}`} key=${c.name} data-tip=${d}
              aria-label=${`${c.name}: ${d}`} tabindex="0"><${x} name=${u.icon} size=${14} />${c.name}</span>`})}
        ${n?.provisional||l?r`<span class="small">
              ${n?.provisional?r`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${l?r`<span class="muted" data-tip=${a}>${n?.provisional?" \xB7 ":""}${l}</span>`:null}
            </span>`:null}
      </div>
      <${Xr} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function Xr(e){let t=w(e.verdict?pt(e.path):null).data;if(!e.verdict)return r`<p class="verdict-line muted">no verdict yet</p>`;let n=R("verdict",e.verdict),s=(t?.entries??[]).find(i=>i.type==="verdict"&&(i.group??e.path)===e.path),o=s?ke(s.id):null;return r`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${x} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${s?r`<span class="small muted" data-tip=${o}>verdict${s.meta?.author?` by ${s.meta.author}`:""}${o?` \xB7 ${V(o)}`:""}</span>`:null}
  </p>`}function Yr({id:e,scope:t}){let n=w(ze(e,t)).data;if(!n)return r`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let s=n.run,o=()=>{navigator.clipboard?.writeText(s.id)},i=()=>{Rt(s.id,t)};return r`
    <h1 class="page-title title" tabindex="-1"><${Se} value=${s.name??s.id} label="the run's name" class="title-edit"
        onSave=${l=>Zn(s.id,t,l.trim())} />
      <${O} spec=${Ge(s.status,s.exit)} word tip=${et(s)} />
      ${s.hidden?r`<${O} spec=${Vr} word tip=${Gr} />`:null}</h1>
    ${s.error?r`<p class="bad-text" data-tip=${s.error}>${s.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${ue(s.steps)}</b> steps</span>
      <span><b>${Te(s.duration_s)}</b></span>
      ${n.progress?r`<${Zr} run=${s} progress=${n.progress} />`:null}
      <span data-tip=${s.created_at}>${V(s.created_at)}</span>
      <${Ns} path=${t} />
      ${s.hidden?r`<${I} icon="eye" label="Promote: count this run in tables, charts and checks" onClick=${i} />`:null}
      <${I} icon="copy" label=${`Copy the run id ${s.id}`} onClick=${o} />
      <${it} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${[...Jr(s),...yt(n)].map(([l,a])=>r`<tr><td class="muted">${l}</td><td>${a}</td></tr>`)}</table>
        ${s.git?.dirty?r`<${wt} run=${s.id} scope=${t} />`:null}
        <div class="menu-list">
          <button type="button" onClick=${()=>D(E(t,{run:s.id}),{replace:!0})}>
            <${x} name="panel-right" size=${15} /> Open in the side panel</button>
          ${s.hidden?r`<button type="button" onClick=${i}><${x} name="eye" size=${15} /> Promote</button>`:null}
          <button type="button" onClick=${o}><${x} name="copy" size=${15} /> Copy the run id</button>
          ${s.git?.commit?r`<button type="button" onClick=${()=>navigator.clipboard?.writeText(s.git.commit)}>
            <${x} name="git-commit" size=${15} /> Copy the commit</button>`:null}
        </div>
      <//>
    </div>
    ${(n.proposals??[]).length?r`<div class="checks">
          ${n.proposals.map(l=>{let a=R("result",l.check);return r`<a class=${`check small tone-${a.tone}`} href=${E(l.group)} data-tip=${l.statement}>
              <${x} name=${a.icon} size=${14} />${l.group==="."?"own proposal":l.group}
              ${l.verdict?r`<${O} spec=${R("verdict",l.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function Zr({run:e,progress:t}){let{epoch:n,total:s,fraction:o,steps_per_epoch:i}=t,l=e.status==="running"&&o!==null&&i&&e.steps_per_s?Te((1-o)*s*i/e.steps_per_s):null;return r`<span>epoch <b>${n}</b>${s?` of ${s}`:""}${o===null?"":` \xB7 ${Math.round(o*100)} % through`}${l?` \xB7 about ${l} left`:""}</span>`}function Ns({path:e}){let t=se(e).main,n=kt(Lt(e,t),e).data?.summary;if(!n)return null;let s=Object.entries(n.config??{}).map(([l,a])=>`${Ae(l)} ${q(a)}`).join(", "),o=ie(e.split("/").pop()??""),i=`${n.stat} of ${n.metric} over ${o?"the run":"all runs"}${s?` (${s})`:""}`;return r`<span data-tip=${i}>
    best <b>${n.label??Ae(`metric.${n.metric}.${n.stat}`)} ${q(n.value)}</b>
    ${o?null:r` · <a href=${re(n.run)}>${n.name}</a>`}
  </span>`}function Jr(e){return[["id",e.id],["host",e.host],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,s])=>[n,String(s)])}var At=80;function Rs({node:e}){let t=J("main"),n=J(e.data?.keys?"keys":""),s=e.props.mode==="run",o=e.props.title??(s?"Config":"Hyperparameters");return r`<${We} id=${`config:${e.id}`} title=${o} open=${e.props.open} result=${t}>
    ${t.data?s?r`<${ct} config=${t.data.config} varying=${qe(n.data)} />`:r`<${Qr} rows=${t.data.config?.rows??[]} />`:r`<div class="skeleton late" style="block-size: 80px"></div>`}
  <//>`}function Qr({rows:e}){let t=new Set(qe({config:{rows:e}})),n=e.filter(([s])=>t.has(s.replace(/^config\./,"")));return n.length?r`<table class="kv small">${n.map(([s,,o])=>{let i=Array.isArray(o)?o.map(q).join(", "):`${q(o.min)} \u2026 ${q(o.max)} \xB7 ${o.distinct} values`;return r`<tr><td data-tip=${s}>${s.replace(/^config\./,"")}</td>
      <td data-tip=${i.length>At?i:void 0}>${i.length>At?`${i.slice(0,At-1)}\u2026`:i}</td></tr>`})}</table>`:r`<p class="muted small">No config differs between the runs.</p>`}var Ls=15e3;function _s({node:e}){let t=Z(W),n=pe(),[s,o]=kn(),i=e.props.code,l=w(o&&i?{method:"code",params:i,scope:null}:null),[a,c]=y(null),[u,$]=y(120),[d,m]=y({error:null,warnings:[]}),f=k=>{he&&console.error(`[block ${e.id}] ${k}`),m(p=>({...p,error:k}))},h=P(()=>{});T(()=>{if(!a)return;m(v=>v.own?{...v,own:!1}:v);let k=!0;Ue.n++;let p=()=>{k&&Ue.n--,k=!1};h.current=p;let b=setTimeout(()=>{k&&f(`no first render within ${Ls/1e3} s`),p()},Ls);return()=>{clearTimeout(b),p()}},[a]),T(()=>{let k=a?.contentWindow;if(!k||l.status!=="ready")return;let p=_=>k.postMessage(_,"*"),b=new Map,v=new Nn,K=_=>{if(_.source!==k)return;let S=_.data;switch(S.type){case"hello":p({type:"init",init:{id:e.id,code:l.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:wn.value,pair:st.value,colormaps:Fe.value,prefs:He(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics,expanded:e.props.expanded?Tn():null}});break;case"sub":if(!Mn.has(S.call.method)){p({type:"result",id:S.id,result:{status:"error",data:null,error:`${S.call.method} is not available in a custom block`,refreshing:!1}});break}b.get(S.id)?.(),b.set(S.id,cn(S.call,ne=>p({type:"result",id:S.id,result:ne})));break;case"unsub":b.get(S.id)?.(),b.delete(S.id);break;case"navigate":S.url.startsWith("/")&&D(S.url);break;case"height":v.accept(performance.now())?$(Math.max(40,S.height)):A("its height keeps changing, so it is fixed at its last height");break;case"chrome":m(ne=>({...ne,own:S.own}));break;case"ready":m(ne=>({...ne,blank:S.blank,overflow:S.overflow})),h.current();break;case"warn":A(S.message);break;case"hover":Pe.set(S.run);break;case"prefs":JSON.stringify(H.value)!==JSON.stringify(S.prefs)&&H.set(S.prefs);break;case"download":case"snapshot":S.href?Pn(S.href,S.name)?performance.now()-j>1e3&&(j=performance.now(),be().download(S.href,S.name)):A(`a download of ${S.name} was refused: only PNG, SVG and CSV files`):A("it draws no SVG or canvas to download");break;case"figure":be().figure(S.spec,S.name).catch(ne=>A(`the PDF failed: ${ne.message}`));break;case"expand":Dn(S.node)&&be().expand(S.node,t);break;case"expand-block":e.props.expanded||be().expand(e,t);break;case"close":e.props.expanded&&_e.set(null);break;case"error":f(S.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,C)),h.current();break;default:break}},A=_=>{he&&console.warn(`[block ${e.id}] ${_}`),m(S=>S.warnings.includes(_)?S:{...S,warnings:[...S.warnings,_]})},j=-1/0,H=He(t.path),U=Pe.subscribe(_=>p({type:"hover",run:_})),L=H.subscribe(_=>p({type:"prefs",prefs:_}));return addEventListener("message",K),p({type:"ping"}),()=>{U(),L(),removeEventListener("message",K);for(let _ of b.values())_()}},[l.status,l.data?.code,a]),T(()=>{let k={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};a?.contentWindow?.postMessage(k,"*")},[t.names,t.colors,t.metrics,a]),T(()=>Fe.subscribe(k=>a?.contentWindow?.postMessage({type:"colormaps",colormaps:k},"*")),[a]),T(()=>{n&&a?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let C=typeof i=="object"?i.path??i.block:String(i??"");xn(e.id,{png:()=>a?.contentWindow?.postMessage({type:"snapshot"},"*")});let g=o&&l.status==="ready"&&!d.error;return r`<div ref=${s} class="custom-block">
    ${d.own?null:r`<div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${g?r`<span class="chart-tools">
            <${I} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>a?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?r`<${I} icon="x" label="Close (Esc)" onClick=${()=>_e.set(null)} />`:r`<${I} icon="maximize" label="Expand" onClick=${()=>be().expand(e,t)} />`}
          </span>`:null}
    </div>`}
    <${oe} caption=${e.props.expanded?void 0:e.props.caption} result=${l}>
      ${d.error?r`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${C})</span>
            <pre class="code">${d.error}</pre>
          </div>`:null}
      ${d.warnings.map(k=>r`<${z} kind="warning">${k}<//>`)}
      ${g?r`<div class="custom-frame" data-frame-blank=${d.blank?"1":void 0} data-frame-overflow=${d.overflow?"1":void 0}>
            <iframe key=${l.data.code} ref=${c} sandbox="allow-scripts" ...${eo()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${u}px`} />
          </div>`:null}
    <//>
  </div>`}function eo(){if(!!1)return{src:tn("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1").replace(/@font-face\s*\{[^}]*\}/g,""),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}var to=8;function Ht(e,t){let n=e?.steps??[];if(t==="step")return{values:n,steps:n};let s=new Map;n.forEach((i,l)=>{let a=e?.clocks?.[l];a!=null&&Number.isFinite(a)&&s.set(a,Math.max(s.get(a)??i,i))});let o=[...s.keys()].sort((i,l)=>i-l);return{values:o,steps:o.map(i=>s.get(i))}}function Kt(e){return Ht(e,"clock").values.length>1}function Is(e,t){let n=0;return e.forEach((s,o)=>{Math.abs(s-t)<Math.abs(e[n]-t)&&(n=o)}),n}function Ut(e,t){let n=0;return e.steps.forEach((s,o)=>{s<=t&&(n=o)}),n}function Os(e,t){return[e.steps[Math.max(0,t-to)],e.steps[t]]}function zs(e,t){let n=new Map;for(let s of e)s.step<=t&&s.step>(n.get(s.run)??-1/0)&&n.set(s.run,s.step);return e.filter(s=>n.get(s.run)===s.step).map(s=>({entry:s,earlier:s.step<t&&t!==1/0}))}function Bs(e,t,n){let s=e?.split(/[/.]/).at(-1);return[...s&&s!=="step"&&t!=null?[`${s} ${q(t)}`]:[],`step ${ue(n)}`].join(" \xB7 ")}function As(e,t){let n=e?.steps?.indexOf(t)??-1;return n<0?null:e?.clocks?.[n]??null}var Ft={k:1,x:0,y:0},Hs=32;function Ks(e,t,n){let s=Math.min(Hs,Math.max(1,e.k));return{k:s,x:Math.min(0,Math.max(t*(1-s),e.x)),y:Math.min(0,Math.max(n*(1-s),e.y))}}function no(e,t,n,s,o,i){let l=Math.min(Hs,Math.max(1,e.k*t)),a=l/e.k;return Ks({k:l,x:n-(n-e.x)*a,y:s-(s-e.y)*a},o,i)}function so(e,t,n,s,o){return Ks({...e,x:e.x+t,y:e.y+n},s,o)}function Us(e){return`translate(${e.x}px, ${e.y}px) scale(${e.k})`}function Fs(){let e=P(null),[t,n]=y(Ft),s=()=>{let a=e.current.getBoundingClientRect();return{w:a.width,h:a.height,left:a.left,top:a.top}},o=(a,c)=>{let{w:u,h:$}=s();n(d=>no(d,a,c?.x??u/2,c?.y??$/2,u,$))};T(()=>{let a=e.current;if(!a)return;let c=u=>{u.preventDefault();let{left:$,top:d}=s();o(Math.exp(-u.deltaY*(u.ctrlKey?.01:.002)),{x:u.clientX-$,y:u.clientY-d})};return a.addEventListener("wheel",c,{passive:!1}),()=>a.removeEventListener("wheel",c)},[]);let i=P(new Map);return{box:e,pose:t,handlers:{onPointerDown:a=>{a.currentTarget.setPointerCapture(a.pointerId),i.current.set(a.pointerId,{x:a.clientX,y:a.clientY})},onPointerMove:a=>{let c=i.current.get(a.pointerId);if(!c)return;let u={x:a.clientX,y:a.clientY},{w:$,h:d,left:m,top:f}=s(),h=[...i.current.entries()].filter(([C])=>C!==a.pointerId).map(([,C])=>C);if(i.current.set(a.pointerId,u),h.length){let[C]=h,g=Math.hypot(c.x-C.x,c.y-C.y),k=Math.hypot(u.x-C.x,u.y-C.y);g>0&&o(k/g,{x:(u.x+C.x)/2-m,y:(u.y+C.y)/2-f})}else n(C=>so(C,u.x-c.x,u.y-c.y,$,d))},onPointerUp:a=>{i.current.delete(a.pointerId)},onPointerCancel:a=>{i.current.delete(a.pointerId)},onDblClick:()=>n(Ft)},zoomBy:o,fit:()=>n(Ft)}}var Wt=new Map;function ro(e,t){return Wt.has(e)||Wt.set(e,new $e({step:t,by:"step"})),Wt.get(e)}function oo(e,t){let[n,s]=y(e);return T(()=>{let o=setTimeout(()=>s(e),t);return()=>clearTimeout(o)},[e]),n}function ao(e){let t=Z(W),n=e.data.main,s=n.params.step,o=`${t.path}\0${e.id}`,i=ro(o,typeof s=="number"?s:null),l=M(i),a=w(n),c=a.data?.meta,u=l.by==="clock"&&Kt(c)?"clock":"step",$=Ee(()=>Ht(c,u),[c,u]),d=l.step===null,m=!(Le||!1)&&(s==="last"||typeof s=="number")&&$.steps.length>1,f=d?$.steps.length-1:Ut($,l.step),h=$.steps[f]??0,C=oo(h,120),g=m&&!d,k=g?{...n,params:{...n.params,step:Os($,Ut($,C)),limit:2e3}}:null,p=w(k),b=g?p.data:a.data,v=P(null);b&&(v.current={entries:b.entries,at:g?C:1/0});let K=s!=="last"&&typeof s!="number",A=v.current?K?v.current.entries.map(U=>({entry:U,earlier:!1})):zs(v.current.entries,v.current.at):[],j=n.params.clock??null,H=U=>{let L=Math.min($.steps.length-1,Math.max(0,U));i.set({...l,step:L===$.steps.length-1?null:$.steps[L]})};return{view:t,base:a,error:p.status==="error"?String(p.error):null,tiles:A,stops:$,i:f,ranged:m,by:u,move:H,clock:j,label:Bs(j,As(c,h),h),clocked:Kt(c),setBy:U=>i.set({step:d?null:h,by:U})}}function io(e,t,n){let s=t.path.split(".").at(-1);return[Qe(de(t.run,e.path),t.path),`${t.run}-${n.replace(/[^\w.-]+/g,"_")}-step${t.step}.${s}`]}function Ws(e,t,n){for(let{entry:s}of t)be().download(...io(e,s,n))}function js({s:e}){if(!e.ranged)return null;let{values:t}=e.stops,n={ArrowLeft:e.i-1,ArrowDown:e.i-1,ArrowRight:e.i+1,ArrowUp:e.i+1,Home:0,End:t.length-1};return r`<div class="scrubber">
    <input type="range" min=${t[0]} max=${t.at(-1)} step="any" value=${t[e.i]} aria-label="Step" aria-valuetext=${e.label}
      onInput=${s=>{let o=s.target,i=Is(t,Number(o.value));o.value=String(t[i]),e.move(i)}}
      onKeyDown=${s=>{s.key in n&&(s.preventDefault(),e.move(n[s.key]))}} />
    <span class="small scrub-label">${e.label}</span>
  </div>`}function Vs({s:e}){if(!e.ranged||!e.clocked)return null;let t=e.clock?.split(/[/.]/).at(-1)??"clock";return r`<button type="button" class="small tool-toggle" aria-pressed=${e.by==="clock"} data-tip=${`Space the stops by ${t}`}
    onClick=${()=>e.setBy(e.by==="clock"?"step":"clock")}>by ${t}</button>`}function Gs({node:e}){let t=ao(e),n=String(e.props.title??e.data.main.params.key);if(e.props.expanded)return r`<${lo} node=${e} s=${t} title=${n} />`;let s=o=>be().expand({...e,props:{...e.props,run:o??t.tiles[0]?.entry.run}},t.view);return r`<div class="block chart-block images-block">
    <${Dt} id=${e.id} title=${n} caption=${e.props.caption}
      tools=${r`<${Vs} s=${t} />`}
      downloads=${{files:()=>Ws(t.view,t.tiles,n)}} onExpand=${()=>s()}>
      ${t.base.status==="error"?r`<${z} kind="error">${t.base.error}<//>`:null}
      ${t.error?r`<${z} kind="error">${t.error}<//>`:null}
      ${t.base.data&&!t.tiles.length?r`<${z}>No images logged.<//>`:null}
      <div class="images">
        ${t.tiles.map(({entry:o,earlier:i})=>r`<figure key=${`${o.run}/${o.path}`} class=${i?"earlier":""} data-tip=${t.view.names.get(o.run)??o.run}>
            <button type="button" class="image-open" aria-label="Open larger" onClick=${()=>s(o.run)}>
              <img src=${Qe(de(o.run,t.view.path),o.path)} alt=${o.caption??n} loading=${Le?"eager":"lazy"} />
            </button>
            <figcaption class="small">step ${ue(o.step)}${o.caption?` \xB7 ${o.caption}`:""}</figcaption>
          </figure>`)}
      </div>
      <${js} s=${t} />
    <//>
  </div>`}function lo({node:e,s:t,title:n}){let{tiles:s}=t,[o,i]=y(null),l=Fs(),a=s.findIndex(h=>h.entry.run===e.props.run),c=Math.min(Math.max(0,o??a),s.length-1),u=s[c],$=u?Qe(de(u.entry.run,t.view.path),u.entry.path):"";T(()=>l.fit(),[$]);let d=h=>i((c+h+s.length)%s.length),m={"+":()=>l.zoomBy(1.5),"=":()=>l.zoomBy(1.5),"-":()=>l.zoomBy(1/1.5),0:l.fit},f=r`
    ${s.length>1?r`<${I} icon="chevron-left" label="Previous image" onClick=${()=>d(-1)} /><${I} icon="chevron-right" label="Next image" onClick=${()=>d(1)} />`:null}
    <${I} icon="minus" label="Zoom out (−)" onClick=${()=>l.zoomBy(1/1.5)} />
    <${I} icon="plus" label="Zoom in (+)" onClick=${()=>l.zoomBy(1.5)} />
    <${I} icon="reset" label="Fit (double-click, 0)" onClick=${l.fit} />
    <${Vs} s=${t} />`;return r`<div class="block chart-block images-block">
    <${Dt} id=${e.id} title=${n} expanded
      notes=${u?[t.view.names.get(u.entry.run)??u.entry.run,`step ${ue(u.entry.step)}`]:[]}
      tools=${f} downloads=${{files:()=>u&&Ws(t.view,[u],n)}}>
      <div class="zoom-box" ref=${l.box} tabindex="0" style=${{touchAction:"none"}} ...${l.handlers}
        onKeyDown=${h=>m[h.key]?.()}>
        ${u?r`<img class="zoom-img" src=${$} alt=${u.entry.caption??n} draggable=${!1} style=${{transform:Us(l.pose)}} />`:null}
      </div>
      <${js} s=${t} />
    <//>
  </div>`}function qs({node:e}){let t=J("main"),n=t.data?.entries??[];return r`<${oe} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?r`<${z}>No text logged.<//>`:null}
    ${n.map(s=>r`<div class="text-entry" key=${`${s.run}/${s.step}`}>
        <div class="muted small">step ${ue(s.step)}${s.caption?` \xB7 ${s.caption}`:""}</div>
        <pre class="code">${s.text??""}</pre>
      </div>`)}
  <//>`}function Xs({node:e}){let n=`section.${Z(W).path}:${e.id}`,[s,o]=y(()=>Le||xe(n,e.props.open!==!1)),i=()=>{fe(n,!s),o(!s)},l=r`${(e.children??[]).map(u=>r`<${ce} key=${u.id} node=${u} />`)}`,a=Z(at);if(!e.props.title)return r`<div class="stack">${l}</div>`;let c=a===e.props.title.toLowerCase();return r`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${s} aria-label=${c?`${s?"Close":"Open"} ${e.props.title}`:void 0}
        data-tip=${c?`${s?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${i}>
      <${x} name=${s?"chevron-down":"chevron-right"} size=${16} />${c?r`<span class="toggle-label code">${a}</span>`:e.props.title}
    </button>
    ${s?r`<div class="stack">${l}</div>`:null}
  </div>`}function Ys({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return r`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>r`<${ce} key=${n.id} node=${n} />`)}
  </div>`}function Vt({node:e,after:t}){let n=Z(W),s=se(n.path),o=e.props.min_width??320,i=e.props.columns,l=i?`grid-template-columns: repeat(${i}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${o}px, 100%), 1fr))`,a=e.children??[],c=a.filter(d=>s.removed.includes(d.id)).map(d=>d.id),u=ln(a.filter(d=>!c.includes(d.id)),s.order[e.id]),$=(d,m)=>{let f=u.map(h=>h.id).filter(h=>h!==d);if(f.splice(f.indexOf(m),0,d),on(n.path,e.id,f),e.id===nn){let h=g=>a.find(k=>k.id===g)?.data?.main?.params?.y?.[0],C=f.map(g=>n.pins.find(k=>k.y===h(g))).filter(g=>!!g);rn(n.path,[...C,...n.pins.filter(g=>!C.includes(g))])}};return r`<div class="grid" style=${l}>
    ${u.map(d=>r`<${co} key=${d.id} node=${d} path=${n.path} span=${s.spans[d.id]??d.props.span??1}
      columns=${i} onDrop=${m=>m!==d.id&&$(m,d.id)} />`)}
    ${t??null}
    ${c.length?r`<div class="grid-note"><button type="button" class="link small" onClick=${()=>Ke(n.path,c)}>${c.length} hidden · show</button></div>`:null}
  </div>`}var jt=[1,2,"full"];function co(e){let[t,n]=y(!1),s=jt[(jt.indexOf(e.span)+1)%jt.length],o=i=>i==="full"?"full width":`${i} column${i===1?"":"s"}`;return r`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${i=>{i.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${i=>{i.preventDefault(),n(!1),e.onDrop(i.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${i=>i.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${x} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${o(e.span)}; click for ${o(s)}`}
        aria-label=${`Width ${o(e.span)}`} onClick=${()=>an(e.path,e.node.id,s)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${ce} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function Gt({root:e}){let t=Z(W),n=se(t.path),s=w({method:"keys",params:{from:t.path},scope:t.path}).data,o=e.props.template;if(!o||!1)return null;let i=new Set(n.removed),l=new Set([...t.charted].filter(([f])=>!i.has(f)).flatMap(([,f])=>f)),a=n.added.filter(f=>!l.has(f)).map(f=>({block:"line",id:`added-${f}`,props:{y:f},data:{main:{...o,params:{...o.params,y:[f]}}}})),c=new Set([...l,...a.filter(f=>!i.has(f.id)).map(f=>f.props.y)]),u=(s?.metrics?.rows??[]).map(f=>f[0]).filter(f=>!c.has(f));if(!s||!(u.length||a.length))return null;let $=f=>[...t.charted].find(([h,C])=>i.has(h)&&C.includes(f))?.[0]??a.find(h=>i.has(h.id)&&h.props.y===f)?.id,d=f=>{let h=$(f);h?Ke(t.path,[h]):tt(t.path,C=>({added:[...C.added,f]}))},m=u.length?r`<div class="add-chart">
        <span class="add-chart-label"><${x} name="plus" size=${16} /> Add a chart</span>
        <${lt} single options=${u} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
          onChange=${([f])=>d(f)} />
      </div>`:null;return r`<${B}><${Vt} node=${{block:"grid",id:"added",props:{},children:a}} after=${m} /><//>`}function Zs({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[s,o]=y(()=>t.find(a=>a.id===n())?.id??t[0]?.id),i=a=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(a)}`),o(a)},l=t.find(a=>a.id===s)??t[0];return Le?r`<div class="stack">${t.map(a=>r`<${ce} key=${a.id} node=${a} />`)}</div>`:r`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(a=>r`<button type="button" role="tab" id=${`tab-${a.id}`} aria-selected=${a.id===l?.id}
          aria-controls=${`panel-${a.id}`} onClick=${()=>i(a.id)}>${a.props.title??a.id}</button>`)}
    </div>
    ${l?r`<div class="stack" role="tabpanel" id=${`panel-${l.id}`} aria-labelledby=${`tab-${l.id}`}>
          ${(l.children??[]).map(a=>r`<${ce} key=${a.id} node=${a} />`)}
        </div>`:null}
  </div>`}function Js({node:e}){let t=J("main"),n=Z(W),s=M(Pe),o=e.props,i=Rn(t.data,o.rows,o.columns,o.lower??{},o.expected??[]),l=F.value.page==="group"?F.value.run:null,a=o.baseline===null||o.baseline===void 0?null:i.find(u=>u.label===String(o.baseline)),c=u=>D(E(n.path,{run:u}),{replace:l!==null});return r`<${oe} title=${o.title} caption=${o.caption} numbered result=${t}>
    ${t.data?r`<div class="table-wrap"><table class="runs scorecard">
          <thead><tr class="small">
            <th data-tip=${o.rows}>${Ae(o.rows)}</th>
            ${o.columns.map(u=>r`<th class="num" data-tip=${u}>${zn(u,n.metrics)}</th>`)}
          </tr></thead>
          <tbody onPointerLeave=${()=>Pe.set(null)}>
            ${i.map(u=>{let $=`${u.runs.includes(l??"")?"selected":""}${u.runs.includes(s??"")?" hovered":""}${u.queued?" queued":""}`;return r`<tr key=${u.label} class=${$} data-tip=${u.runs.length?`${u.runs.length} run${u.runs.length>1?"s":""}`:void 0}
                  onClick=${u.runs.length?()=>c(u.runs[0]):void 0}
                  onPointerEnter=${()=>Pe.set(u.runs[0]??null)}>
                <td>${u.label}${u===a?r` <${Ce} tip="the others are compared to this row">baseline<//>`:null}${u.queued?r` <${Ce}>queued<//>`:null}</td>
                ${u.scores.map((d,m)=>uo(d,u.live,a?.scores[m]??null))}
              </tr>`})}
          </tbody>
        </table></div>`:r`<div class="skeleton late" style="block-size: 120px"></div>`}
  <//>`}function uo(e,t,n){if(!e)return r`<td class="num muted">–</td>`;let s=n&&n!==e?`${e.mean-n.mean>=0?"+":"\u2212"}${q(Math.abs(e.mean-n.mean))} against the baseline`:"",o=`${St(e.mean)}${e.std===null?"":` \xB1 ${St(e.std)}`}, ${e.n} run${e.n>1?"s":""}${s?`. ${s}`:""}`,i=`num score${e.best?" best":""}${t?" live":""}`;return r`<td class=${i} style=${e.shade===null?void 0:`--shade: ${e.shade}`} data-tip=${o}>
    ${q(e.mean)}${e.std===null?null:r`<span class="spread"> ± ${q(e.std)}</span>`}</td>`}var Qs={section:Xs,row:Ys,grid:Vt,line:Hn,table:jn,scorecard:Js,stat:Wn,images:Gs,text:qs,proposal:bs,note:Es,output:Cs,config:Rs,memory:vs,groups:ys,notes:ws,tabs:Zs,scatter:Kn,bar:Un,histogram:Fn,data_table:In,timeline:On,custom:_s,markdown:Ss},po=new Set(["line","scatter","bar","histogram"]);function ce({node:e}){return po.has(e.block)?r`<${mo} node=${e} />`:r`<${Pt} node=${e} blocks=${Qs} />`}function mo({node:e}){let t=Z(W);return se(t.path).removed.includes(e.id)?r`<div class="grid-note"><button type="button" class="link small" onClick=${()=>Ke(t.path,[e.id])}>1 hidden · show</button></div>`:r`<${Pt} node=${e} blocks=${Qs} />`}function er(e,t){let n=e.split(`
`),s=t.split(`
`),o=n.length,i=s.length,l=Array.from({length:o+1},()=>new Uint32Array(i+1));for(let $=o-1;$>=0;$--)for(let d=i-1;d>=0;d--)l[$][d]=n[$]===s[d]?l[$+1][d+1]+1:Math.max(l[$+1][d],l[$][d+1]);let a=[],c=0,u=0;for(;c<o&&u<i;)n[c]===s[u]?(a.push({kind:"same",text:n[c]}),c++,u++):l[c+1][u]>=l[c][u+1]?a.push({kind:"removed",text:n[c++]}):a.push({kind:"added",text:s[u++]});for(;c<o;)a.push({kind:"removed",text:n[c++]});for(;u<i;)a.push({kind:"added",text:s[u++]});return a}function tr(e,t=3){let n=[],s=0;for(;s<e.length;){if(e[s].kind!=="same"){n.push(e[s++]);continue}let o=s;for(;o<e.length&&e[o].kind==="same";)o++;let i=s===0?0:t,l=o===e.length?0:t;o-s>i+l+1?n.push(...e.slice(s,s+i),{kind:"skip",count:o-s-i-l},...e.slice(o-l,o)):n.push(...e.slice(s,o)),s=o}return n}var qt={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",config:"config",timeline:"timeline",proposal:"predictions"};function nr(e){if(qt[e.block])return qt[e.block];if(e.block==="row"||e.block==="grid"){let n=new Set((e.children??[]).map(o=>qt[o.block])),[s]=n;if(n.size===1&&s)return s}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function xt(e){let t=w(Xe(e.path)),n=pe(),s=N(t.data),o=Ee(()=>ot(s.map(m=>m["run.id"]),n),[t.data,n]),i=Ee(()=>new Map(s.map(m=>[m["run.id"],m["run.name"]??m["run.id"]])),[t.data]),l=se(e.path),a=e.plain?"view plain":"sections view";if(!e.view)return r`<div class=${a}>${e.before}
      ${e.plain?r`<div class="skeleton late" style="block-size: 320px"></div>`:r`<${B} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let c=e.view.view,u={path:e.path,colors:o,names:i,metrics:e.view.metrics??{},charted:Xt(c),pins:l.main??e.view.pins??[]};if(e.plain)return r`<div class=${a}><${W.Provider} value=${u}><${ce} node=${c} /><//></div>`;let $=c.block==="section"&&!c.props.title?c.children??[]:[c],d=$.map(m=>Xt(m).size>0).lastIndexOf(!0);return r`<div class=${a}>${e.before}
    <${W.Provider} value=${u}>
      ${$.map((m,f)=>{let h=nr(m);return r`<${Jt} key=${m.id}><${B} label=${h}><${at.Provider} value=${h}><${ce} node=${m} /><//><//>
          ${f===d?r`<${Gt} root=${c} />`:null}<//>`})}
      ${d===-1?r`<${Gt} root=${c} />`:null}
    <//>
  </div>`}function Xt(e,t=new Map){e.block==="line"&&t.set(e.id,e.data?.main?.params?.y??[]);for(let n of e.children??[])Xt(n,t);return t}function sr(e){if(null)return r`<div class="view-source small"><${x} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=M(F),s=n.page==="group"&&n.version,o=t.versions?r`<a href=${E(e.path,{history:!0})}><${x} name="history" size=${14} /> history (${t.versions})</a>`:null,i;switch(t.source){case"draft":i=r`draft <b>${t.draft}</b>`;break;case"view":i=r`${t.title?r`<em>${t.title}</em> · `:null}saved ${V(ke(t.version))} by ${t.author??"unknown"}`;break;default:i=r`the built-in view`}return r`<div class="view-source small">
    <${x} name="layout" size=${14} /><span>${i}</span>
    ${s?r`<a href=${E(e.path)}>an older version · show the current one</a>`:null}
    ${o}
    ${t.outdated?.length&&!s?r`<${$o} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||s?null:r`<${fo} path=${e.path} />
        <${ho} path=${e.path} view=${t} />`}
  </div>`}function $o(e){let[t,n]=y(null),s=e.outdated.map(i=>i.name).join(", ");return r`<button type="button" class="link small" onClick=${async()=>{n(null);try{await Jn(e.path)}catch(i){n(i.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${s} exists; update re-pins this view to it (a new version)`}>
      <${x} name="update" size=${14} /> update ${s}</button>
    ${t?r`<span class="bad-text small">${t}</span>`:null}`}function fo(e){let[t,n]=y(null);return r`<button type="button" class="link small" onClick=${async()=>{n(null);try{Ie.set(await dt(e.path,null,""))}catch(o){n(o.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${x} name="file-text" size=${14} /> add text</button>
    ${t?r`<span class="bad-text small">${t}</span>`:null}`}function ho(e){let t=se(e.path),n=sn(t),[s,o]=y(!1),[i,l]=y(e.view.title??""),[a,c]=y(e.view.finding??""),[u,$]=y(null),[d,m]=y(!1);if(!n&&!s)return null;let f=async h=>{h.preventDefault(),m(!0),$(null);try{let C={charts:t.charts,view:t.view,added:t.added,removed:t.removed,order:t.order,spans:t.spans,main:t.main};await G("save_view",{path:e.path,prefs:C,title:i,finding:a}),tt(e.path,()=>({view:{},charts:{},added:[],removed:[],order:{},spans:{},main:null})),Re(g=>["view","view_history","summary"].includes(g.method)&&g.scope===e.path),o(!1)}catch(C){$(C.message)}finally{m(!1)}};return s?r`<form class="save-form" onSubmit=${f}>
    <${je} label="Title"><input value=${i} onInput=${h=>l(h.target.value)} /><//>
    <${je} label="Finding"><input value=${a} placeholder="the key result in one sentence"
        onInput=${h=>c(h.target.value)} /><//>
    <div class="save-actions">
      <${Q} type="submit" icon=${d?"hourglass":"save"} disabled=${d}>${d?"Saving\u2026":"Save as view"}<//>
      <${Q} icon="x" kind="quiet" onClick=${()=>o(!1)}>Cancel<//>
      ${u?r`<span class="bad-text small">${u}</span>`:null}
    </div>
  </form>`:r`<${Q} icon="save" class="save-view" onClick=${()=>o(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function rr(e){let t=w(ls(e.path)),n=t.data?.entries??[],[s,o]=y(null),i=s??n.slice(0,2).map(a=>a.version).reverse(),l=a=>{let c=i.includes(a)?i.filter(u=>u!==a):[...i,a].slice(-2);o(c.sort())};return t.status==="error"?r`<${z} kind="error">${t.error}<//>`:r`<section class="history">
    ${t.data&&!n.length?r`<${z}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((a,c)=>r`<li key=${a.version} class=${i.includes(a.version)?"picked":""}>
          <label><input type="checkbox" checked=${i.includes(a.version)} onChange=${()=>l(a.version)} />
            <span class="num muted" data-tip=${a.version}>${V(a.time)}</span>
            <b>${a.title??"untitled"}</b><span class="muted">${a.author??""}</span>
            ${a.message?r`<span>${a.message}</span>`:null}</label>
          <a href=${c===0?E(e.path):E(e.path,{version:a.version})}
            onClick=${u=>{u.preventDefault(),D(c===0?E(e.path):E(e.path,{version:a.version}))}}>${c===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${i.length===2?r`<${go} path=${e.path} a=${i[0]} b=${i[1]} />`:null}
  </section>`}function go(e){let t=a=>({method:"view_show",params:{group:e.path,version:a},scope:e.path}),n=w(t(e.a)).data,s=w(t(e.b)).data,o=w(ve(e.path,e.a)).data,i=w(ve(e.path,e.b)).data,l=n&&s?tr(er(n.yaml,s.yaml)):[];return r`<div class="compare">
    <h3 class="block-title heading">Changes from ${V(ke(e.a))} to ${V(ke(e.b))}</h3>
    <pre class="diff code">${l.map(a=>a.kind==="skip"?r`<div class="diff-skip">⋯ ${a.count} unchanged lines</div>`:r`<div class=${`diff-${a.kind}`}>${a.kind==="added"?"+ ":a.kind==="removed"?"\u2212 ":"  "}${a.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${o?.title??e.a}</h3><${xt} path=${e.path} view=${o} plain /></div>
      <div><h3 class="block-title heading">${i?.title??e.b}</h3><${xt} path=${e.path} view=${i} plain /></div>
    </div>
  </div>`}function or(e){return cs(e.path),e.history?r`<div class="page"><div class="sections">
      <${B} label=${ar(e.path)}><${Bt} path=${e.path} /><//>
      <${B} label="history"><${rr} path=${e.path} /><//>
    </div></div>`:r`<div class="page">
    <${bo} path=${e.path} version=${e.version??null} draft=${e.draft??null} hiddenRuns=${e.hiddenRuns??!1} />
  </div>`}function bo(e){let t=se(e.path).main,n=kt(ve(e.path,e.version,e.draft,t),`${e.path}|${e.version}|${e.draft}`);T(()=>{n.status==="ready"&&requestAnimationFrame(fn)},[n.status==="ready"]),T(()=>{let o=i=>Ms(i.target.closest?.(".chart-frame")??null);return addEventListener("click",o,!0),()=>removeEventListener("click",o,!0)},[]);let s=r`
    <${B} label=${ar(e.path)}>
      <${Bt} path=${e.path} finding=${n.data?.finding} />
      ${n.data?r`<${sr} path=${e.path} view=${n.data} />`:null}
    <//>
    ${ie(e.path.split("/").pop()??"")?null:r`${e.hiddenRuns?r`<${Ps} path=${e.path} />`:null}<${Ds} path=${e.path} />`}`;return n.status==="error"?r`<div class="sections">${s}
      <${B} label="view">
        ${vo(e.path,n.error)?r`<${z} kind="warning">${n.error} The page fills in once the remote answers again.<//>`:r`<${z} kind="error">${n.error}<//>`}
      <//>
    </div>`:r`<${xt} path=${e.path} view=${n.data} before=${s} />`}function ar(e){return ie(e.split("/").pop()??"")?"run":"group"}function vo(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function ir(e){T(()=>{Ne(ve(e.id)).then(n=>D(E(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=w(ve(e.id));return t.status==="error"?r`<div class="page"><${z} kind="error">${t.error}<//></div>`:r`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var yo={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},Yt=20,Be=-1,wo=[["day",86400],["week",7*86400],["month",30*86400]];function cr(e){let t=N(w(me()).data).map(a=>a.path),n=w({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),s=w({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});Ze("Timeline",N(n.data).filter(a=>a["run.status"]==="running").length);let o=Date.now()/1e3,i=N(n.data).filter(a=>a["run.created_at"]).map((a,c)=>({id:a["run.id"],name:a["run.name"]??a["run.id"],group:a["run.group"],status:a["run.status"],start:Date.parse(a["run.created_at"])/1e3,end:a["run.ended_at"]?Date.parse(a["run.ended_at"])/1e3:o,lane:c})),l=(s.data?.entries??[]).map(a=>({id:a.id,type:a.type,group:a.group,description:a.description,t:Date.parse(ke(a.id))/1e3}));return r`<div class="page timeline-page"><div class="sections">
    <${B} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${je} label="Group" inline>
          <select value=${e.from} onChange=${a=>D(nt(a.target.value),{replace:!0})}>
            ${t.map(a=>r`<option value=${a}>${a==="."?"everything":a}</option>`)}
          </select><//>
        <span class="muted small">${i.length} runs · ${l.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${B} label="runs">
      ${n.status==="error"?r`<${z} kind="error">${n.error}<//>`:null}
      ${n.data&&s.data?r`<${ko} bars=${i} marks=${l} />`:r`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function ko(e){let t=pe(),n=P(null),s=[...e.bars.flatMap(g=>[g.start,g.end]),...e.marks.map(g=>g.t)],o=s.length?lr(Math.min(...s),Math.max(...s)):lr(Date.now()/1e3-86400,Date.now()/1e3),[i,l]=y(o),a=e.bars.length,c=Math.min(900,Math.max(160,(a+1.5)*Yt+40)),$=Bn(n,An,t?(g=>{let k=Ln(i[0],i[1]),p=v=>g.colors[yo[v]??"muted"],b=v=>g.colors[v==="verdict"?"good":v==="decision"?"accent":v==="question"?"warn":"muted"];return{style:yn(g),height:c,x:{range:i,log:!1,format:v=>_n(v,k.step),label:"",splits:k.at},y:{range:[Be-.8,a+.5],log:!1,reverse:!0,label:"",size:150,splits:a<=40?[Be,...e.bars.map(v=>v.lane)]:[Be],format:v=>v===Be?"notes":To(e.bars[Math.round(v)]?.name??"")},draw:({ctx:v,x:K,y:A,px:j,focused:H})=>{let U=Yt*.62*j;for(let L of e.bars){let _=K(L.start),S=Math.max(3*j,K(L.end)-_);v.fillStyle=H!==null&&H!==L.id?vn(p(L.status),.35):p(L.status),v.beginPath(),v.roundRect(_,A(L.lane)-U/2,S,U,3*j),v.fill()}for(let L of e.marks){let _=K(L.t),S=A(Be),ne=(H===L.id?6:4.5)*j;v.fillStyle=b(L.type),v.beginPath(),v.moveTo(_,S-ne),v.lineTo(_+ne,S),v.lineTo(_,S+ne),v.lineTo(_-ne,S),v.closePath(),v.fill()}},hit:(v,K,A,j)=>{if(Math.abs(K-j(Be))<Yt/2){let L=Eo(e.marks,_=>Math.abs(A(_.t)-v),8);return L?{key:L.id,rows:Co(L)}:null}let H=Math.round((K-j(0))/(j(1)-j(0))),U=e.bars.find(L=>L.lane===H&&A(L.start)-3<=v&&v<=Math.max(A(L.end),A(L.start)+3)+3);return U?{key:U.id,rows:xo(U)}:null},onClick:v=>{let K=e.marks.find(A=>A.id===v);K?D(E(K.group,{drawer:!0})):D(re(v))}}})(t):null,[i,e.bars,e.marks],t),d=g=>{if(!$.current)return;g.preventDefault();let k=$.current.xAt(g.clientX),p=Math.exp(g.deltaY*.0015);l(([b,v])=>Zt([k-(k-b)*p,k+(v-k)*p],o))},m=P(null),f=g=>m.current={x:g.clientX,range:i},h=g=>{if(!m.current||!$.current||!(g.buttons&1))return;let k=(g.clientX-m.current.x)*$.current.xPerPixel(),[p,b]=m.current.range;Math.abs(g.clientX-m.current.x)>3&&l(Zt([p-k,b-k],o))},C=Math.max(...s,Date.now()/1e3);return r`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${wo.map(([g,k])=>r`<button type="button" role="radio" aria-checked=${Math.abs(i[1]-i[0]-k)<1}
          onClick=${()=>l(Zt([C-k,C+k*.02],[Math.min(o[0],C-k),o[1]]))}>last ${g}</button>`)}
      <button type="button" role="radio" aria-checked=${i[0]===o[0]&&i[1]===o[1]} onClick=${()=>l(o)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${c}px`}
      onWheel=${d} onPointerDown=${f} onPointerMove=${h} onPointerUp=${()=>m.current=null}></div>
    <p class="muted small">${So(t)}</p>
  </div>`}function xo(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:V(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:Te(e.end-e.start),color:null}]}function Co(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:V(new Date(e.t*1e3).toISOString()),color:null}]}function So(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function Eo(e,t,n){let s=null,o=n;for(let i of e){let l=t(i);l<o&&([s,o]=[i,l])}return s}function lr(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function Zt([e,t],n){let s=Math.min(n[1]-n[0],Math.max(60,t-e)),o=Math.max(n[0],Math.min(e,n[1]-s));return[o,o+s]}function To(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function ur(){let e=M(_e),t=P(null);if(T(()=>{let o=t.current;if(!o||!e)return;o.showModal();let i=()=>_e.set(null);return o.addEventListener("close",i),()=>o.removeEventListener("close",i)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},s=String(n.props.title??n.props.y??"Chart");return r`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${s} closedby="any">
    <${W.Provider} value=${e.view}><${ce} node=${n} /><//>
  </dialog>`}function dr(e,t){let n=e.toLowerCase(),s=t.toLowerCase();if(!n)return 1;let o=s.indexOf(n);if(o>=0)return 100-Math.min(o,50)-s.length/100;let i=0,l=0;for(let a of s)if(a===n[i]?i++:i>0&&l++,i===n.length)return 40-Math.min(l,39);return 0}function mr(e){let[t,n]=y(e.query),[s,o]=y(0),i=P(null),l=N(w(me()).data),a=N(w(mt()).data);T(()=>{let p=i.current;p.showModal();let b=()=>te.set(null);p.addEventListener("close",b);let v=!1,K=H=>{let U=p.getBoundingClientRect();return H.clientX<U.left||H.clientX>U.right||H.clientY<U.top||H.clientY>U.bottom},A=H=>v=K(H),j=H=>v&&K(H)&&p.close();return"closedBy"in HTMLDialogElement.prototype||(p.addEventListener("pointerdown",A),p.addEventListener("pointerup",j)),()=>{p.removeEventListener("close",b),p.removeEventListener("pointerdown",A),p.removeEventListener("pointerup",j)}},[]);let c=()=>i.current?.close(),u=p=>()=>D(p),$=F.value,d=$.page==="group"?$.path:".",m=(p,b,v,K)=>({section:"Commands",label:p,detail:b,sym:{icon:v,tone:"muted",label:p},run:K}),h=[...l.map(p=>({section:"Groups",label:p.path==="."?"local":p.path,detail:`${p.runs} runs${p.proposal?` \xB7 ${p.proposal}`:""}`,sym:R("research",p.status),run:u(E(p.path))})),...a.map(p=>({section:"Runs",label:p["run.name"]??p["run.id"],detail:`${p["run.status"]} \xB7 ${p["run.path"]}`,sym:R("run",p["run.status"]),run:u(E(p["run.path"]))})),m("Theme: light","","sun",()=>rt("light")),m("Theme: dark","","moon",()=>rt("dark")),m("Theme: follow the system","","monitor",()=>rt("system")),m("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),m("Show notes and timeline","i","file-text",u(E(d,{drawer:!0}))),m("Show or hide the sidebar","\u2318B","panel-left",()=>ee.set(!ee.value)),m(ae.value?"Resume live updates":"Pause live updates","p",ae.value?"play":"pause",()=>ae.set(!ae.value)),m("Keyboard shortcuts","?","keyboard",()=>ye.set(!0)),m("Settings","","settings",u("/settings/appearance"))].map(p=>({it:p,s:Math.max(dr(t,p.label),dr(t,p.detail)*.5)})).filter(p=>p.s>0).sort((p,b)=>b.s-p.s||pr(p.it.section)-pr(b.it.section)).slice(0,60).map(p=>p.it),C=p=>{p&&(c(),p.run())},g=p=>{if(p.key==="ArrowDown")o(Math.min(h.length-1,s+1));else if(p.key==="ArrowUp")o(Math.max(0,s-1));else if(p.key==="Enter")C(h[s]);else return;p.preventDefault()},k="";return r`<dialog class="sheet" ref=${i} aria-label="Search" closedby="any">
    <div class="palette-input"><${x} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${h[s]?`pal-${s}`:void 0}
        onInput=${p=>{n(p.target.value),o(0)}} onKeyDown=${g} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${h.map((p,b)=>{let v=p.section!==k&&!t?k=p.section:null;return r`${v?r`<li class="palette-head small" role="presentation">${v}</li>`:null}
          <li id=${`pal-${b}`} class="item" role="option" aria-selected=${b===s}
              onMouseMove=${()=>o(b)} onClick=${()=>C(p)}>
            <${O} spec=${p.sym} /><span class="label">${p.label}</span><span class="detail small">${p.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function pr(e){return["Groups","Runs","Commands"].indexOf(e)}function Ct(e,t=[]){let n=new Map,s=(a,c={})=>({path:a,name:a==="."?"local":a.split("/").pop(),runs:c.runs??0,running:c.running??0,failed:(c.failed??0)+(c.killed??0)+(c.lost??0),status:c.status??null,children:[]});for(let a of e)n.set(a.path,s(a.path,a));(t.length===0||t.some(a=>a.name==="."))&&!n.has(".")&&n.set(".",s("."));for(let a of t){let c=a.name;n.has(c)||n.set(c,s(c)),Object.assign(n.get(c),{state:a.state,error:a.error})}for(let a of n.values()){if(X(a.path))continue;let c=a.path.lastIndexOf("/"),u=c<0?".":a.path.slice(0,c);(n.get(u)??n.get(Me(a.path))??n.get(".")).children.push(a)}for(let a of n.values())a.children.sort((c,u)=>c.name.localeCompare(u.name));let i=[...n.values()].filter(a=>a.path!=="."&&X(a.path)).sort((a,c)=>a.name.localeCompare(c.name)),l=n.get(".");return l?[l,...i]:i}function $r(e,t,n,s=new Set){let o=[],i=n.toLowerCase(),l=a=>{(!i||a.path.toLowerCase().includes(i)||fr(a,i))&&(o.push(a),(i||(X(a.path)?!s.has(a.path):t.has(a.path)))&&a.children.forEach(l))};return e.forEach(l),o}function fr(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||fr(n,t))}function hr(e,t){if(!t||X(t))return e;let n=t.split("/"),s=new Set(e);for(let o=t.startsWith("@")?2:1;o<n.length;o++)s.add(n.slice(0,o).join("/"));return s.size===e.size?e:s}function gr(e,t){if(X(t))return e;let n=t.lastIndexOf("/"),s=n<0?".":t.slice(0,n),o=i=>i.path===s?i:i.children.map(o).find(l=>l)??null;return e.map(o).find(i=>i)?.children??[]}function br(e){return X(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function vr(){let e=M(F),t=w(me()),[n,s]=y(()=>new Set(xe("open",[]))),[o,i]=y(()=>new Set(xe("closed-hosts",[]))),[l,a]=y(""),c=P(null),u=e.page==="group"?e.path:null,$=Ct(N(t.data),t.data?.meta?.sources??[]),d=$r($,n,l,o),m=g=>X(g)?!o.has(g):n.has(g),f=(g,k)=>{let p=k??!m(g);if(X(g)){let v=new Set(o);p?v.delete(g):v.add(g),fe("closed-hosts",[...v]),i(v);return}let b=new Set(n);p?b.add(g):b.delete(g),fe("open",[...b]),s(b)},h=P(u);return T(()=>{let g=hr(n,u);g!==n&&(fe("open",[...g]),s(g)),u!==h.current&&u&&!X(u)&&o.has(Me(u))&&f(Me(u),!0),h.current=u},[u]),r`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${x} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${l} aria-label="Filter groups"
        onInput=${g=>a(g.target.value)} />
    </label>
    <div class="tree" ref=${c} onKeyDown=${g=>{let k=[...c.current?.querySelectorAll("a.tree-item")??[]],p=k.indexOf(document.activeElement),b=d[p];switch(g.key){case"ArrowDown":k[Math.min(k.length-1,p+1)]?.focus();break;case"ArrowUp":k[Math.max(0,p-1)]?.focus();break;case"ArrowRight":b?.children.length&&f(b.path,!0);break;case"ArrowLeft":b?.children.length&&m(b.path)?f(b.path,!1):b&&k[d.findIndex(v=>v.path===Po(b.path))]?.focus();break;default:return}g.preventDefault()}} role="tree">
      ${d.map(g=>r`<${Mo} key=${g.path} node=${g} current=${g.path===u}
        open=${m(g.path)||!!l} filtering=${!!l} onToggle=${()=>f(g.path)} />`)}
    </div>
  </nav>`}function Mo(e){let t=e.node,n=()=>Ye(t.path),s=t.children.length>0,o=t.state==="unreachable";return r`<a class=${`tree-item${e.current?" current":""}${X(t.path)?" source-root":""}`} href=${E(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${s?e.open:void 0}
      style=${`padding-inline-start:${8+br(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${i=>{i.metaKey||i.ctrlKey||(i.preventDefault(),e.current&&s&&!e.filtering?e.onToggle():D(E(t.path)))}}>
    <span class=${`twisty${s?" expandable":""}`} aria-disabled=${s&&e.filtering?"true":void 0}
      onClick=${i=>{s&&(i.preventDefault(),i.stopPropagation(),e.filtering||e.onToggle())}}>
      ${s?r`<${x} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    ${X(t.path)?r`<${O} size=${14} spec=${{icon:o?"cloud-off":"server",tone:"muted",label:o?`Unreachable: ${t.error??"no answer"}`:t.path==="."?"This machine":`Remote host ${t.name}`}} />`:null}
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?r`<${O} spec=${R("run","running")} size=${14} />`:null}
      ${t.failed?r`<${O} spec=${{...R("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function Po(e){if(X(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function wr(){let e=M(F),t=M(ee),n=M(te),s=M(ye),o=P(null);T(()=>$n(()=>o.current),[]),T(()=>(addEventListener("keydown",yr),()=>removeEventListener("keydown",yr)),[]);let i=e.page==="group"&&e.drawer,l;switch(e.page){case"group":l=r`<${or} key=${`${e.path} ${e.version} ${e.draft} ${e.history} ${e.hiddenRuns}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} hiddenRuns=${e.hiddenRuns} />`;break;case"run":l=r`<${ir} id=${e.id} />`;break;case"settings":l=r`<${ms} />`;break;case"timeline":l=r`<${cr} key=${e.from} from=${e.from} />`;break;default:l=r`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return he||!1?r`<main class="main render-main" ref=${o}>${l}</main>`:r`<div class=${`shell${t?"":" no-sidebar"}${i?" with-drawer":""}`}>
    <${fs} />
    ${t?r`<${vr} />`:null}
    <main class="main" ref=${o}>${l}</main>
    ${i?r`<${Ts} path=${e.path} run=${e.run} />`:null}
    <${hs} />
    ${n!==null?r`<${mr} query=${n} />`:null}
    ${s?r`<${No} />`:null}
    <${ur} />
  </div>`}function yr(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),te.set(te.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),ee.set(!ee.value);return}if(e.key==="Escape"){if(te.value!==null||ye.value)return;let s=F.value;return s.page==="group"&&s.run?D(E(s.path,{drawer:!0}),{replace:!0}):s.page==="group"&&s.drawer?D(E(s.path),{replace:!0}):void 0}if(t||e.altKey||ds(e)||te.value!==null||ye.value)return;let n=F.value;switch(e.key){case"/":e.preventDefault(),te.set("");break;case"?":ye.set(!ye.value);break;case"p":ae.set(!ae.value);break;case"i":n.page==="group"&&D(E(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":ee.set(!ee.value);break;case"[":case"]":n.page==="group"&&Do(n.path,e.key==="]"?1:-1);break}}async function Do(e,t){let n=await Ne(me()),s=gr(Ct(N(n),n?.meta?.sources??[]),e),o=s.findIndex(l=>l.path===e),i=s[o+t];i&&D(E(i.path))}function No(){let e=P(null);return T(()=>{let t=e.current;t.showModal();let n=()=>ye.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),r`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${ht.map(([t,n])=>r`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${Q} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}hn();if(he){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(ge.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Ue.n,gn&&Cn()}Vn();var Ro=G("meta").then(e=>(he&&(e={...e,settings:{...e.settings,theme_mode:ge.value}}),gt(e),e));!he&&!!1&&mn(async()=>{let[e,t]=await Promise.all([Ro,G("meta")]);e.bundle!==t.bundle?location.reload():gt(t)});Qt(r`<${wr} />`,document.getElementById("app"));
