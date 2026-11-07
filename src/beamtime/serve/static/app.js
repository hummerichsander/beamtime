import{$ as W,A as jt,Aa as mn,B as ue,Ba as pn,C as Re,Ca as $n,D as Gt,E as We,Ea as fn,F as pt,Fa as hn,G as me,Ga as gn,H as Xt,Ha as vn,I as $t,Ia as bn,J as qe,Ja as yn,K as V,Ka as wn,L as J,La as kn,M as ie,N as Xe,O as Yt,P as Ie,Q as Oe,S as Jt,T as Zt,U as w,V as P,W as Ye,X as se,Y as z,Z as _,_ as ze,a as s,aa as Qt,ba as I,ca as ae,d as K,da as Be,e as Le,ea as ft,f as Se,fa as Je,g as mt,ga as Ze,h as k,ha as E,i as Bt,ia as gt,j as te,ja as Ae,k as At,ka as Qe,l as Ht,la as en,m as Kt,ma as vt,n as Ce,na as He,o as ne,oa as et,p as C,pa as tn,q as Ge,qa as bt,r as de,ra as nn,s as Pe,sa as sn,t as we,ta as an,u as G,ua as on,v as q,w as Ut,xa as rn,y as L,ya as ln,z as Ft,za as cn}from"./chunks/chunk-W47VUAXT.js";import{a as Ot,b as zt}from"./chunks/chunk-O2K4N3UR.js";import{A as Wt,B as qt,C as F,F as ve,G as ke,H as xe,I as U,J as ht,U as dn,V as un,c as Rt,e as y,f as T,g as It,h as O,i as _e,j as ee,m as ye,n as N,o as he,p as ge,u as Vt,w as Ve}from"./chunks/chunk-24GOVU2B.js";import"./chunks/chunk-VC46IEJQ.js";function Ee(e,t){Ce(n=>t.includes(n.method)&&n.scope!==null&&(n.scope==="."||e===n.scope||e.startsWith(`${n.scope}/`)||n.scope.startsWith(`${e}/`)))}var yt=["notes","timeline","groups","check","card","memory_show","status"];async function tt(e,t){let n=e.meta??{};await K("note_add",{group:e.group,type:t.type??e.type,description:t.description??e.description,body:t.body??e.body??"",supersedes:e.id,resolves:n.resolves??[],completes:n.completes??[],evidence:n.evidence??[],...n.proposal?{proposal:n.proposal,verdict:n.verdicts??{},overall:n.overall??null}:{}}),Ee(e.group,yt)}async function xn(e,t,n,a){await K("note_add",{group:e,type:t,description:n,body:a}),Ee(e,yt)}async function Sn(e,t){await K("memory_update",{group:e,body:t}),Ee(e,["memory_show","status"])}async function Cn(e,t){let n=await K("proposal_show",{group:e}),a=Object.fromEntries(Object.entries(n.proposal??{}).filter(([o])=>!["schema","author","user","supersedes"].includes(o)));await K("proposal_set",{group:e,proposal:{...a,statement:t}}),Ee(e,["groups","proposal_show","check","summary"])}async function En(e){await K("note_rm",{note:e.id}),Ee(e.group,yt)}async function Tn(e,t,n){await K("name",{run:e,name:n}),Ee(t,["card","runs","groups","summary","series"])}async function nt(e,t,n){let a=await K("view_text",{path:e,id:t,text:n});return Ce(o=>["view","view_history"].includes(o.method)&&o.scope===e),a.id}async function Mn(e){await K("view_upgrade",{group:e}),Ce(t=>["view","view_history"].includes(t.method)&&t.scope===e)}var Te=new ye(null);async function Nn(e,t){return await K("set",{key:e,value:t}),K("meta")}var le=()=>({method:"groups",params:{from:".",everywhere:!0},scope:"."}),pe=(e,t=null,n=null)=>({method:"view",params:{path:e,...t?{version:t}:{},...n?{draft:n}:{}},scope:e}),wt=e=>({method:"summary",params:{path:e},scope:e}),Me=e=>({method:"groups",params:{from:e,depth:0},scope:e}),Dn=e=>({method:"check",params:{group:e},scope:e}),_n=e=>({method:"proposal_show",params:{group:e},scope:e}),Ne=(e,t)=>({method:"card",params:{run:Pe(e,t)},scope:t}),Ln=(e,t)=>({method:"output",params:{run:Pe(e,t),tail:30},scope:t}),Ke=e=>({method:"runs",params:{from:e,select:["run.name","run.status"],limit:1e4},scope:e}),st=e=>({method:"notes",params:{from:e,limit:20,full:!0,current:!0},scope:e}),Pn=e=>({method:"timeline",params:{from:e,limit:30},scope:e}),Rn=()=>({method:"status",params:{},scope:"."}),at=()=>({method:"runs",params:{from:".",select:["run.name","run.path","run.status","run.ended_at"],sort:["-run.created_at"],limit:5e3},scope:"."});function Ue(e){for(let t of[pe(e),Me(e),Ke(e),wt(e)])mt(t);Se(pe(e)).then(t=>{for(let n of In(t.view))mt(n)}).catch(()=>{})}function In(e){return e?[...Is.has(e.block)?[]:Object.values(e.data??{}),...(e.children??[]).flatMap(In)]:[]}var Is=new Set(["line","custom"]),On=e=>({method:"view_history",params:{group:e},scope:e});var kt="/static/favicon.svg",ot=null;async function Os(){if(ot)return ot;let e=new Image;e.src=kt,await e.decode();let t=32,n=document.createElement("canvas");n.width=n.height=t;let a=n.getContext("2d");if(!a)return kt;a.drawImage(e,0,0,t,t),a.beginPath(),a.arc(t-6,t-6,6,0,Math.PI*2);let o=getComputedStyle(document.documentElement).getPropertyValue("--accent").trim();return a.fillStyle=o||"#2f5aa8",a.fill(),ot=n.toDataURL("image/png"),ot}function zs(e){if(!1)return;let t=document.querySelector("link[rel=icon]");if(t instanceof HTMLLinkElement){if(!e){t.type="image/svg+xml",t.href=kt;return}Os().then(n=>{t.type="image/png",t.href=n})}}function Fe(e,t=0){T(()=>{document.title=`${t?`(${t}) `:""}${e} \xB7 Beamtime`,zs(t>0)},[e,t])}function zn(e){let t=ne(e.split("/").pop()??""),n=k(t?null:Me(e)),a=k(t?Ne(e.split("/").pop()??"",e):null),o=t?a.data?.run.name??a.data?.run.id??e:e==="."?"local":e.split("/").pop()??e,i=t?a.data?.run.status==="running"?1:0:_(n.data)[0]?.running??0;Fe(o,i)}var Z=new ye(he("sidebar",!0)),Q=new ye(null),$e=new ye(!1),fe=new ye(null);Z.subscribe(e=>ge("sidebar",e));var Bn=he("visit",Date.now());ge("visit",Date.now());function An(e){let t=e.target;return!!t&&(t.tagName==="INPUT"||t.tagName==="TEXTAREA"||t.isContentEditable)}var rt=[["\u2318K, /","search groups, runs and commands"],["\u2191 \u2193 \u2190 \u2192","move in the group tree"],["[  ]","previous and next sibling group"],["i","open or close the context drawer"],["\u2318B, b","show or hide the sidebar"],["p","pause or resume live updates"],["Esc","clear the selection, close the drawer"],["?","this list"]];var Bs=[["system","monitor","System"],["light","sun","Light"],["dark","moon","Dark"]];function it(e){fe.set(e),We.set(e.theme),Ve.set(e.colormaps),e.settings?.theme_mode&&me.set(e.settings.theme_mode),$t()}var Hn=0;async function xt(e,t){let n=++Hn;e==="theme_mode"&&(me.set(t),$t());let a=await Nn(e,t);n===Hn&&it(a)}function Kn(){let e=N(me),t=ie(),n=N(fe),[a,o]=y(null);Fe("Settings");let i=(l,d)=>{o(null),xt(l,d).catch(p=>o(p.message))},c=n?.settings??{},r=(l,d,p)=>s`
    <label class="field-label small" for=${`setting-${l}`}>${d}</label>
    <span class="input body">
      <select id=${`setting-${l}`} value=${c[l]} onChange=${m=>i(l,m.target.value)}>
        ${p.map(m=>s`<option value=${m}>${m}</option>`)}
      </select>
    </span>`;return s`<div class="page settings"><div class="sections">
    <${I} label="settings">
      <h1 class="page-title title" tabindex="-1">Settings</h1>
      <p class="muted small">Changes are written to <code>${c.file??"beamtime.yaml"}</code>, the project's settings.</p>
      ${a?s`<${z} kind="error">${a}<//>`:null}
    <//>
    <${I} label="appearance">
      <div class="settings-rows">
        <span class="field-label small">Mode</span>
        <div class="segmented" role="radiogroup" aria-label="Theme mode">
          ${Bs.map(([l,d,p])=>s`<button type="button" role="radio" aria-checked=${e===l} onClick=${()=>i("theme_mode",l)}>
            <${w} name=${d} size=${15} />${p}</button>`)}
        </div>
        ${r("theme","Theme",n?.themes??[])}
      </div>
      <p class="muted small">Shown: <b>${t?.name??"\u2013"}</b>. Your own theme files recolor this layout: they go in <code>themes/</code> next to
        beamtime.yaml. Colormaps are chosen in each chart's settings.</p>
      ${(n?.theme?.problems??[]).map(l=>s`<${z} kind="warning">${l}<//>`)}
    <//>
    <${I} label="figures">
      <div class="settings-rows">
        <span class="field-label small">Style sheets</span>
        ${(n?.figure_styles??[]).length?s`<${Ze} options=${n.figure_styles} value=${c.figure_style??[]} label="Style sheets"
              placeholder="Add a style" onChange=${l=>i("figure_style",l)} />`:s`<span class="muted small"><code>${JSON.stringify(c.figure_style??[])}</code>; choosing others needs the figures
              extra: <code>uv add matplotlib scienceplots</code></span>`}
      </div>
      <p class="muted small">PDF downloads are drawn with <code>plt.style.use(${JSON.stringify(c.figure_style??[])})</code>, in this order
        (later sheets override earlier ones). Without LaTeX, <code>no-latex</code> is added for <code>science</code>. Your own
        <code>.mplstyle</code> files anywhere in the project are listed too.</p>
    <//>
    <${I} label="keyboard">
      <table class="kv">${rt.map(([l,d])=>s`<tr><td><kbd class="small">${l}</kbd></td><td>${d}</td></tr>`)}</table>
    <//>
    <${I} label="about">
      <table class="kv">
        <tr><td class="muted">version</td><td>${n?.version}</td></tr>
        <tr><td class="muted">root</td><td><code class="code">${n?.root}</code></td></tr>
        ${(n?.sources??[]).map(l=>s`
          <tr><td class="muted">${l.name}</td><td><code class="code">${l.logdir}</code> (${l.kind}, ${l.state})</td></tr>`)}
      </table>
    <//>
  </div></div>`}var Un={system:"light",light:"dark",dark:"system"},As={system:"monitor",light:"sun",dark:"moon"};function Fn(){let e=N(fe),t=N(me),n=N(Z);return s`<header class="topbar">
    <${W} icon="panel-left" label=${n?"Hide the sidebar (\u2318B)":"Show the sidebar (\u2318B)"}
      pressed=${n} onClick=${()=>Z.set(!n)} />
    <a class="project heading" href="/f/local">${e?.project??"Beamtime"}</a>
    <button type="button" class="search input body" onClick=${()=>Q.set("")} aria-label="Search (⌘K)">
      <${w} name="search" size=${15} /><span class="search-label small">Search groups, runs, commands</span><kbd class="small">⌘K</kbd>
    </button>
    <div class="topbar-actions">
      <${Hs} />
      <${W} icon=${As[t]} label=${`Theme: ${t==="system"?"follows the system":t} (switch to ${Un[t]})`}
        onClick=${()=>{xt("theme_mode",Un[t])}} />
      <a class="icon-button" href=${Ge(q.value.page==="group"?q.value.path:".")} aria-label="Timeline"
        data-tip="Timeline of runs and notes"><${w} name="clock" size=${16} /></a>
      <a class="icon-button" href="/settings/appearance" aria-label="Settings" data-tip="Settings"><${w} name="settings" size=${16} /></a>
    </div>
  </header>`}function Hs(){let t=(k(le()).data?.meta?.sources??[]).filter(n=>n.name!=="local");return t.length?s`${[{name:"local",state:"connected"},...t].map(n=>s`<a class=${`source small ${n.state}`}
      href=${C(n.name==="local"?".":n.name)}
      data-tip=${n.state==="connected"?`${n.name}: connected`:`${n.name}: unreachable. ${n.error??""}`}>
      <${w} name=${n.state==="connected"?"server":"cloud-off"} size=${15} /> ${n.name}</a>`)}`:s`<span class="source small" data-tip="Sources: this machine. Remotes are configured under remotes: in the settings.">
      <${w} name="server" size=${15} /> local</span>`}function Ks(e){let[t,n]=y(Date.now());return T(()=>{let a=setInterval(()=>n(Date.now()),e);return()=>clearInterval(a)},[e]),t}function Us(e){return typeof e=="number"?e*1e3:typeof e=="string"?Date.parse(e):NaN}function jn(){let e=N(At),t=N(te),n=N(Ht),a=N(q),o=Ks(5e3),i=k(Rn()).data,c=_(k(at()).data),r=N(fe),l=i?.daemon,d=i?.runs?.running??0,p=c.filter(M=>M["run.status"]==="failed"&&Us(M["run.ended_at"])>Bn).length,m=i?.meta?.freshness,[b,f,h]=t?["paused","paused","Live updates are paused (p)"]:e==="live"&&l?["",`live \xB7 updated ${U(new Date(n).toISOString(),o)}`,`beamtime serve, pid ${l.pid}`]:e==="live"?["wait","connected; the indexer is not running","Start it with: beamtime serve"]:e==="connecting"?["wait","connecting\u2026","Reconnecting to beamtime serve"]:["off","offline","The server is not reachable"];return s`<footer class="statusbar small">
    <span class="status-item" data-tip=${h}><span class=${`live-dot ${b}`}></span>${f}</span>
    ${d?s`<button type="button" class="status-item" data-tip="List the running runs" onClick=${()=>Q.set("running")}>
          <${w} name="circle-dot" size=${14} class="tone-accent" />${d} running</button>`:null}
    ${p?s`<button type="button" class="status-item tone-bad" data-tip="Runs that failed since your last visit" onClick=${()=>Q.set("failed")}>
          <${w} name="circle-x" size=${14} />${p} failed since your last visit</button>`:null}
    ${m?.behind?s`<span class="status-item warn-text" data-tip=${m.text}><${w} name="hourglass" size=${14} />${m.behind} runs behind</span>`:null}
    ${m?.damaged?.length?s`<span class="status-item warn-text" data-tip=${m.damaged.join(`
`)}><${w} name="triangle-alert" size=${14} />${m.damaged.length} unreadable</span>`:null}
    <span class="spacer"></span>
    ${a.page==="group"&&a.run?s`<span class="status-item"><${w} name="activity" size=${14} />1 run selected</span>`:null}
    <${W} icon=${t?"play":"pause"} label=${t?"Resume live updates (p)":"Pause live updates (p)"}
      pressed=${t} onClick=${()=>te.set(!t)} />
    ${r?.outdated?s`<span class="status-item warn-text" data-tip="The page was rebuilt after this server started; some actions need the new server code.">
          restart <code>beamtime serve</code> to update</span>`:null}
    <span class="status-item">${r?.version?`beamtime ${r.version}`:""}</span>
  </footer>`}var Gn=null;function lt(e){let t=O(null),[n,a]=y(null),[o,i]=y(!1),[c,r]=y(!1);T(()=>{let m=!0;return Gn??=import("./chunks/md-SW3VT2BQ.js"),Gn.then(b=>b.render(e.text??"")).then(b=>m&&a(b)),()=>{m=!1}},[e.text]),It(()=>{let m=t.current;if(!m||!e.clamp)return;let b=()=>r(m.scrollHeight>m.clientHeight+2),f=new ResizeObserver(b);return f.observe(m),()=>f.disconnect()},[e.clamp,n]);let l=e.clamp&&!o,d=`md${l?" clamped":""}`,p=l?`--clamp:${e.clamp}`:"";return s`<div class=${`md-wrap ${e.class??""}`}>
    ${n===null?s`<div class=${d} ref=${t} style=${p}>
          ${(e.text??"").split(/\n{2,}/).map(m=>s`<p>${m}</p>`)}
        </div>`:s`<div class=${d} ref=${t} style=${p} dangerouslySetInnerHTML=${{__html:n}}></div>`}
    ${e.clamp&&(c||o)?s`<button type="button" class="link small more" onClick=${()=>i(!o)}>${o?"less":"more"}</button>`:null}
  </div>`}function be(e){let[t,n]=y(!!e.startEditing),[a,o]=y(e.value),[i,c]=y(null),[r,l]=y(null),d=O(null),p=O(!1);T(()=>c(null),[e.value]),T(()=>{!t||!d.current||(d.current.focus(),e.startEditing?d.current.select():d.current.setSelectionRange(d.current.value.length,d.current.value.length))},[t]);let[m,b]=y(!1),f=e.locked??void 0,h=$=>{if(!$.target.closest("a, button, input, summary")){if(f)return b(!0);$.preventDefault(),o(i??e.value),l(null),p.current=!1,n(!0)}},M=()=>{p.current=!0,n(!1),l(null),e.onCancel?.()},g=async()=>{if(p.current)return;p.current=!0;let $=e.multiline?a.trim():a.replace(/\s*\n\s*/g," ").trim();if($===e.value.trim()||!$&&!e.multiline)return M();n(!1),c($);try{await e.onSave($)}catch(v){c(null),o($),l(v.message),p.current=!1,n(!0)}},x=$=>{if($.key==="Escape")return $.preventDefault(),$.stopPropagation(),M();$.key!=="Enter"||$.isComposing||$.keyCode===229||(!e.multiline||$.metaKey||$.ctrlKey)&&($.preventDefault(),g())};if(t)return s`<div class=${`editable editing ${e.class??""}`}>
      <textarea ref=${d} class="edit-field" value=${a} aria-label=${e.label} placeholder=${e.placeholder}
        rows=${e.multiline?Math.min(18,Math.max(4,a.split(`
`).length+1)):1}
        onInput=${$=>o($.target.value)} onKeyDown=${x} onBlur=${g}></textarea>
      <span class="edit-hint small">${e.multiline?"\u2318Enter saves":"Enter saves"} · Esc cancels${r?s` · <span class="bad-text">${r}</span>`:null}</span>
    </div>`;let u=i??e.value;return s`<div class=${`editable${f?" locked":""}${i!==null?" saving":""} ${e.class??""}`}
      tabindex=${0} role="button" aria-label=${f?`${e.label}: ${f}`:`Edit ${e.label}`}
      data-tip=${f} onClick=${h} onBlur=${()=>b(!1)}
      onKeyDown=${$=>$.key==="Enter"&&$.target===$.currentTarget&&h($)}>
    ${u.trim()?e.render?e.render(u):u:s`<span class="muted">${e.placeholder??"Click to write"}</span>`}
    ${m&&f?s`<span class="edit-hint small locked-why" role="status"><${w} name="lock" size=${14} /> ${f}</span>`:null}
  </div>`}function St(e){let t=[];if(e.effect!==void 0&&e.effect!==null){let n=e.ci?` [${F(e.ci[0])}, ${F(e.ci[1])}]`:"";t.push(`${e.effect>=0?"+":""}${F(e.effect)}${n}`)}return e.threshold!==void 0&&e.threshold!==null&&t.push(`needs ${e.op} ${F(e.threshold)}`),e.points&&t.push(`${e.points} point${e.points>1?"s":""}`),e.detail&&t.push(e.detail),t.join(" \xB7 ")}function Ct(e){if(!e)return["",void 0];let[t,...n]=e.split("; ");return[t,n.length?e:void 0]}function Vn({node:e}){let t=J("proposal"),n=J("check"),a=t.data,o=n.data;if(!a)return s`<${se} result=${t}><div class="skeleton late" style="block-size: 90px"></div><//>`;let i=a.proposal??{},c=(a.versions??[]).filter(l=>l.version!==a.version),r=!e.props.of||e.props.of===".";return s`<${se} title="Predictions" result=${t} class="proposal">
    ${r?null:s`<p class="statement">${i.statement}</p>`}
    ${i.rationale?s`<p class="rationale prose">${i.rationale}</p>`:null}
    <div class="predictions">
      ${(o?.predictions??[]).map(l=>s`<div class="prediction" key=${l.name}>
          <${P} spec=${E("result",l.result)} />
          <span class="pname">${l.name}</span>
          <span class="pdetail num small">${St(l)}</span>
        </div>`)}
    </div>
    ${c.length?s`<${ft} summary=${`${c.length} earlier version${c.length>1?"s":""}`}>
          ${c.map(l=>s`<p class="small"><code>${l.version}</code> ${l.statement}
            <span class="muted">(${l.runs} runs, check ${l.check??"\u2013"})</span></p>`)}
        <//>`:null}
  <//>`}function Wn({node:e}){let t=J("main"),n=e.data?.main.params.group??".",a=t.data?.chain??[],o=a.find(r=>r.group===n)??null,i=a.filter(r=>r.group!==n),c=o?.notes_since?"out of date":o?`version ${o.versions??1}`:"none yet";return s`<${ze} id=${`memory:${e.data?.main.scope??e.id}`} title=${e.props.title??"Memory"}
      count=${t.data?c:void 0} open=${!1} result=${t}
      action=${s`<${P} spec=${{icon:"circle-help",tone:"muted",label:js}} />`}>
    <${be} value=${o?.body??""} label="the memory" multiline class="markdown prose"
      placeholder="No memory yet: write what this group has established, in a few lines."
      render=${r=>s`<${lt} text=${r} />`} onSave=${r=>Sn(n,r)} />
    ${o&&(o.body?.length>(t.data?.budget??1/0)||o.notes_since>=Fs)?s`<p class="memory-meta small warn-text">${o.body?.length>t.data.budget?`${o.body.length} characters, beyond the budget of ${t.data.budget}`:`${o.notes_since} notes since this version`}: ask your agent to compact it (Beamtime's memory prompt), or run
          <code>beamtime memory update ${n}</code>.</p>`:null}
    ${o?s`<p class="memory-meta small">${o.author} · covers notes until ${o.covers_until?.slice(0,10)}
          ${o.notes_since?s` · <span class="warn-text">${o.notes_since} newer note${o.notes_since>1?"s":""}</span>`:null}</p>`:null}
    ${i.length?s`<p class="memory-meta small">Memory above this group: ${i.map((r,l)=>s`${l?", ":""}<a href=${C(r.group)}>${r.group==="."?"local":r.group}</a>`)}</p>`:null}
  <//>`}var Fs=5,js="One memory per group: a short summary of what its notes established, rewritten as new versions (the newest counts). Groups above have their own.",Gs="Notes at or below this page: each is its own file. Editing writes a new version that replaces it; deleting moves it to the trash.";function qn({node:e}){let t=J("main"),n=e.data?.main.params.from??".",a=_(t.data).filter(o=>o.path!==n);return s`<${se} title=${e.props.title} count=${t.data?String(a.length):void 0} result=${t}>
    ${t.data&&!a.length?s`<${z}>No groups below.<//>`:null}
    <div class="group-list">
      ${a.map(o=>{let[i,c]=Ct(o.progress),r=(o.failed??0)+(o.killed??0)+(o.lost??0);return s`<a class="group-row" key=${o.path} href=${C(o.path)}
            onPointerEnter=${()=>Ue(o.path)} onFocus=${()=>Ue(o.path)}>
          <${P} spec=${E("research",o.status)} />
          <span class="gname heading">${o.path.split("/").pop()}</span>
          <span class="gfacts small">
            ${o.status!=="concluded"?s`<span class=${`tone-${E("research",o.status).tone}`}>${E("research",o.status).label}</span>`:null}
            ${o.check?s`<${P} spec=${E("result",o.check)} word />`:null}
            ${o.verdict?s`<${P} spec=${E("verdict",o.verdict)} />`:null}
            ${i?s`<span data-tip=${c}>${i}</span>`:null}
            <span class="num"><b>${o.runs}</b> runs</span>
            ${o.running?s`<${P} spec=${E("run","running")} />`:null}
            ${r?s`<span class="tone-bad num" data-tip="failed, killed or lost"><${w} name="circle-x" size=${14} /> ${r}</span>`:null}
          </span>
          ${o.proposal?s`<span class="gstatement caption">${o.proposal}</span>`:null}
        </a>`})}
    </div>
  <//>`}function Xn({node:e}){let t=J("main"),n=e.data?.main.params.from??".",[a,o]=y(!1),i=(t.data?.entries??[]).filter(r=>!String(r.state??"").startsWith("superseded")),c=t.data?.meta?.matched??i.length;return s`<${ze} id=${`notes:${e.data?.main.scope??e.id}`} title=${e.props.title??"Notes"}
      count=${t.data?String(c):void 0} result=${t}
      action=${s`<${P} spec=${{icon:"circle-help",tone:"muted",label:Gs}} />
        ${s`<${W} icon="plus" label="Add a note" onClick=${()=>o(!0)} />`}`}>
    <div class="notes">
      ${a?s`<${qs} group=${n} onDone=${()=>o(!1)} />`:null}
      ${t.data&&!i.length&&!a?s`<p class="muted small">No notes yet.</p>`:null}
      ${i.map(r=>s`<${ct} key=${r.id} note=${r} scope=${n} />`)}
      ${t.data?.more&&e.data?s`<${Yn} call=${e.data.main} before=${i[i.length-1]?.id} scope=${n} />`:null}
    </div>
  <//>`}var Vs=20;function Yn(e){let[t,n]=y(!1),a=t&&e.before?{...e.call,params:{...e.call.params,before:e.before,limit:Vs}}:null,o=k(a);if(!t)return s`<button type="button" class="link small older-notes" onClick=${()=>n(!0)}>Show older notes</button>`;if(o.status==="error")return s`<p class="bad-text small">${o.error}</p>`;let i=o.data?.entries??[];return s`${o.data?null:s`<div class="skeleton" style="block-size: 40px"></div>`}
    ${i.map(c=>s`<${ct} key=${c.id} note=${c} scope=${e.scope} />`)}
    ${o.data?.more?s`<${Yn} call=${e.call} before=${i[i.length-1]?.id} scope=${e.scope} />`:null}`}var Ws=["observation","decision","idea","question","theory"];function Jn(e){return(e?.note_types??Ws).filter(t=>t!=="verdict")}function qs(e){let t=Jn(N(fe)),[n,a]=y("observation"),[o,i]=y(""),[c,r]=y(""),[l,d]=y(null),[p,m]=y(!1),b=async h=>{if(h.preventDefault(),!o.trim())return d("give the note a title");m(!0);try{await xn(e.group,n,o.trim(),c.trim()),e.onDone()}catch(M){d(M.message),m(!1)}};return s`<form class="note new-note" onSubmit=${b} onKeyDown=${h=>{h.key==="Escape"&&e.onDone(),h.key==="Enter"&&(h.metaKey||h.ctrlKey)&&b(h)}}>
    <div class="note-line">
      <span class="input body"><select class="note-type" value=${n} aria-label="Note type" onChange=${h=>a(h.target.value)}>
        ${t.map(h=>s`<option value=${h}>${h}</option>`)}
      </select></span>
      <span class="input body new-note-field"><input class="new-note-title" value=${o} placeholder="What did you see, decide or wonder?" aria-label="Title"
        autofocus onInput=${h=>i(h.target.value)} /></span>
    </div>
    <span class="input small"><textarea class="new-note-body" rows="4" value=${c} placeholder="Details in Markdown (optional); [[run-id]] links a run"
      aria-label="Details" onInput=${h=>r(h.target.value)}></textarea></span>
    <div class="save-actions">
      <${ae} type="submit" icon=${p?"hourglass":"plus"} disabled=${p}>${p?"Adding\u2026":"Add note"}<//>
      <${ae} icon="x" kind="quiet" onClick=${e.onDone}>Cancel<//>
      <span class="muted small">⌘Enter adds, Esc cancels</span>
      ${l?s`<span class="bad-text small">${l}</span>`:null}
    </div>
  </form>`}function Xs({note:e}){let t=Jn(N(fe)).filter(n=>n!==e.type);return e.type==="verdict"?s`<span class="sym tone-accent" data-tip="a verdict's type can't change; write a new note">
      <${w} name=${E("note","verdict").icon} size=${15} /></span>`:s`<${Je} icon=${E("note",e.type).icon} label="Change the note's type" title="Note type">
    <div class="menu-list">
      ${t.map(n=>s`<button type="button" key=${n} onClick=${()=>tt(e,{type:n})}>
        <${w} name=${E("note",n).icon} size=${15} /> ${n}</button>`)}
    </div>
  <//>`}function ct(e){let t=e.note,[n,a]=y(!!e.open),[o,i]=y(!1),c=e.scope!==void 0&&t.group&&t.group!==e.scope?t.group:null,r=t.id.slice(0,15).replace(/(\d{4})(\d{2})(\d{2})-(\d{2})(\d{2})(\d{2})/,"$1-$2-$3T$4:$5:$6Z"),l=t.meta?.author;return s`<article class=${`note${n?" open":""}`}>
    <div class="note-line" onClick=${d=>!d.target.closest(".editable, a, .note-delete, .popover-wrap")&&a(!n)}>
      <button type="button" class="note-toggle" aria-expanded=${n} aria-label=${n?"Close the note":"Open the note"}>
        <${w} name=${n?"chevron-down":"chevron-right"} size=${14} /></button>
      <${Xs} note=${t} />
      <${be} value=${t.description} label="the note's title" class="note-title heading" render=${Js}
        onSave=${d=>tt(t,{description:d})} />
      ${t.overall?s`<${P} spec=${E("verdict",t.overall)} />`:null}
      ${t.state?s`<${Qt} tone="warn">${t.state}<//>`:null}
      ${c?s`<a class="note-group small" href=${C(c)} data-tip="from this group">${Ys(c,e.scope)}</a>`:null}
      <span class="note-meta small">${l?`${l} \xB7 `:""}${U(r)}</span>
      ${s`<${W} icon="trash" label="Delete this note (moves it to the trash)" class="note-delete" pressed=${o}
        onClick=${d=>{d.stopPropagation(),i(!o)}} />`}
    </div>
    ${o?s`<div class="note-confirm small" role="alertdialog" aria-label="Delete this note?">
          <span>Delete this note${t.meta?.supersedes?" and its earlier versions":""}? It moves to the trash.</span>
          <${ae} icon="trash" kind="danger" onClick=${()=>{En(t)}}>Delete<//>
          <${ae} icon="x" kind="quiet" onClick=${()=>i(!1)}>Cancel<//>
        </div>`:null}
    ${n?s`<${be} value=${t.body??""} label="the note" multiline class="note-body prose markdown"
          placeholder="Add details in Markdown" render=${d=>s`<${lt} text=${d} />`}
          onSave=${d=>tt(t,{body:d})} />`:null}
  </article>`}function Ys(e,t){let n=t==="."?e:e.startsWith(`${t}/`)?e.slice(t.length+1):e,a=n.split("/").pop()??n;return ne(a)?a.slice(-8):n}function Zn({node:e}){let t=J("main"),n=t.data?.lines??[],a=t.data?.meta??{},o=s`<${w} name="terminal" size=${15} /> ${e.props.title??"Output"}
    <span class="muted small">${t.data?`${a.total_lines??n.length} lines${(a.shown??0)<(a.total_lines??0)?`, last ${a.shown}`:""}`:""}</span>`;return s`<${se} result=${t}>
    <${ft} summary=${o} open=${e.props.open}>
      <pre class="log code">${n.join(`
`)}</pre>
    <//>
  <//>`}function Qn({node:e}){let t=ee(V);return s`<${se} title=${e.props.title} caption=${e.props.caption} class="markdown-block">
    <${be} value=${e.props.text??""} label="the text" multiline class="markdown prose"
      startEditing=${Te.value===e.id} onCancel=${()=>Te.set(null)}
      placeholder="Empty: saving removes the panel" render=${n=>s`<${lt} text=${n} />`}
      onSave=${n=>(Te.set(null),nt(t.path,e.id,n))} />
  <//>`}function es({node:e}){return s`<${z} kind=${e.props.kind??"info"}>${e.props.text}<//>`}function Js(e){return(e??"").split(/(\[\[[^\]]+\]\]|`[^`]+`)/g).map(n=>{if(n.startsWith("[[")){let a=n.slice(2,-2),[o]=a.split(/[#@]/),i=o.split("/").pop()??"";return s`<a href=${ne(i)?de(i):C(o)}>${a}</a>`}return n.startsWith("`")?s`<code>${n.slice(1,-1)}</code>`:n})}function ts(e){let t=()=>L(C(e.path),{replace:!0});return s`<aside class="drawer" aria-label=${e.run?"Run":"Notes and timeline"}>
    <div class="drawer-head small">
      <span class="status-item"><${w} name=${e.run?"activity":"file-text"} size=${15} />
        ${e.run?"Run":"Notes and timeline"}</span>
      <${W} icon="x" label="Close (Esc)" onClick=${t} />
    </div>
    ${e.run?s`<${Zs} id=${e.run} scope=${e.path} />`:s`<${Qs} path=${e.path} />`}
  </aside>`}function Zs({id:e,scope:t}){let n=k(Ne(e,t)).data,a=k(Ln(e,t)).data,o=k(Ke(t)).data,i=k({method:"keys",params:{from:t},scope:t}).data,c=ie(),r=_e(()=>Xe(_(o).map(m=>m["run.id"]),c).get(e),[o,c,e]);if(!n)return s`<div class="drawer-body"><div class="skeleton late" style="block-size: 220px"></div></div>`;let l=n.run,d=Object.entries(n.metrics??{}),p=Vt(r,c);return s`<div class="drawer-body">
    <h3 class="heading"><span class=${p.class} style=${p.style}></span>
      <a href=${de(e)}>${l.name}</a></h3>
    <p class="facts small">
      <${P} spec=${E("run",l.status)} word />
      <span><b>${ke(l.steps)}</b> steps</span>
      <span><b>${xe(l.duration_s)}</b></span>
      <span data-tip=${l.created_at}>${U(l.created_at)}</span>
    </p>
    ${l.error?s`<pre class="log code bad-text">${l.error}</pre>`:null}
    <h4 class="small">Config</h4>
    <${Qe} config=${n.config??{}} varying=${Ae(i)} />
    ${d.length?s`<h4 class="small">Metrics</h4>
          <table class="kv small">
            <tr><th></th><th class="num">last</th><th class="num">min</th><th class="num">max</th></tr>
            ${d.map(([m,b])=>s`<tr><td>${m}</td><td class="num"><b>${F(b.last)}</b></td>
              <td class="num">${F(b.min)}</td><td class="num">${F(b.max)}</td></tr>`)}
          </table>`:null}
    ${n.cited_by?.length?s`<h4 class="small">Cited by</h4>${n.cited_by.map(m=>s`<p class="small"><${P} spec=${E("note",m.type)} /> ${m.description}</p>`)}`:null}
    <h4 class="small">Events</h4>
    ${(n.events??[]).slice(-8).map(m=>s`<div class="event small"><span class="muted num">${m.t?.slice(5,16).replace("T"," ")}</span>
        <${w} name=${gt(m.type)} size=${14} /><span>${m.description}</span></div>`)}
    <h4 class="small">Output</h4>
    <pre class="log code">${(a?.lines??[]).join(`
`)}</pre>
  </div>`}function Qs({path:e}){let t=k(st(e)).data,n=k(Pn(e)).data;return s`<div class="drawer-body">
    <h4 class="small" style="margin-block-start: 0">Notes</h4>
    ${t&&!t.entries.length?s`<p class="muted small">No notes yet.</p>`:null}
    <div class="notes">${(t?.entries??[]).filter(a=>!String(a.state??"").startsWith("superseded")).map(a=>s`<${ct} key=${a.id} note=${a} />`)}</div>
    <h4 class="small">Timeline</h4>
    ${(n?.entries??[]).slice().reverse().map(a=>s`<div class="event small"><span class="muted num">${a.t?.slice(5,16).replace("T"," ")}</span>
        <${w} name=${a.kind==="note"?"file-text":gt(a.type)} size=${14} />
        <span>${a.run?s`<a href=${de(a.run)}>${a.run.slice(-8)}</a> `:null}${a.description??a.type}</span></div>`)}
  </div>`}var Et=["failed","killed","lost"];function Tt(e){let t=we(e.path),n=t==="."?e.path:e.path.slice(t.length+1),a=G(e.path)?[]:n.split("/"),o=a.length&&ne(a[a.length-1])?a[a.length-1]:null,i=a.slice(0,-1),c=r=>[...t==="."?[]:[t],...i.slice(0,r+1)].join("/");return s`<header class="header">
    <nav class="crumbs small" aria-label="Breadcrumb">
      ${a.length?s`<a href=${C(t)}>${t==="."?"local":t}</a>`:null}
      ${i.map((r,l)=>s`<span>/</span><a href=${C(c(l))}>${r}</a>`)}
    </nav>
    ${o?s`<${na} id=${o} scope=${e.path} />`:s`<${ea} path=${e.path} />`}
    ${e.finding?s`<p class="finding prose">${e.finding}</p>`:null}
  </header>`}function ea({path:e}){let t=_(k(Me(e)).data)[0]??null,n=e==="."?"local":e.split("/").pop();if(!t)return s`<h1 class="page-title title" tabindex="-1">${n}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=Et.reduce((o,i)=>o+(t[i]??0),0);return s`
    <h1 class="page-title title" tabindex="-1">${n} <${P} spec=${E("research",t.status)} word /></h1>
    <p class="facts">
      <span><b>${t.runs}</b> run${t.runs===1?"":"s"}</span>
      ${t.running?s`<span><b>${t.running}</b> running</span>`:null}
      ${t.finished?s`<span><b>${t.finished}</b> finished</span>`:null}
      ${a?s`<span class="tone-bad" data-tip=${Et.filter(o=>t[o]).map(o=>`${t[o]} ${o}`).join(", ")}>
            <${w} name="circle-x" size=${15} /> <b>${a}</b> ${a===1?Et.find(o=>t[o]):"ended early"}</span>`:null}
      ${t.notes?s`<span><b>${t.notes}</b> note${t.notes===1?"":"s"}</span>`:null}
      <${ss} path=${e} />
    </p>`}function ns({path:e}){let t=_(k(Me(e)).data)[0]??null,n=k(t?.proposal?Dn(e):null).data,a=k(t?.proposal?_n(e):null).data;if(!t?.proposal)return null;let o=a?.proposal?.rationale,i=a?.versions?.find(l=>l.version===a.version)?.frozen?"Frozen: runs recorded this proposal. Supersede it with `beamtime proposal set --reason`.":void 0,[c,r]=Ct(n?.progress?.text??t.progress);return s`<${I} label="proposal">
    <div class="proposal">
      <div class="statement">
        <${be} value=${t.proposal} label="the proposal's statement" locked=${a?i:"Loading the proposal\u2026"}
          render=${l=>s`<span data-tip=${i?void 0:o}>${l}</span>`}
          onSave=${l=>Cn(e,l)} />
      </div>
      <div class="checks">
        ${(n?.predictions??[]).map(l=>{let d=E("result",l.result),p=St(l),m=p?`${d.label}: ${p}`:d.label;return s`<span class=${`check small tone-${d.tone}`} key=${l.name} data-tip=${m}
              aria-label=${`${l.name}: ${m}`} tabindex="0"><${w} name=${d.icon} size=${14} />${l.name}</span>`})}
        ${n?.provisional||c?s`<span class="small">
              ${n?.provisional?s`<span class="tone-warn" data-tip="the plan is not complete yet">provisional</span>`:null}
              ${c?s`<span class="muted" data-tip=${r}>${n?.provisional?" \xB7 ":""}${c}</span>`:null}
            </span>`:null}
      </div>
      <${ta} path=${e} verdict=${t.verdict} />
    </div>
  <//>`}function ta(e){let t=k(e.verdict?st(e.path):null).data;if(!e.verdict)return s`<p class="verdict-line muted">no verdict yet</p>`;let n=E("verdict",e.verdict),a=(t?.entries??[]).find(i=>i.type==="verdict"&&(i.group??e.path)===e.path),o=a?ve(a.id):null;return s`<p class="verdict-line">
    <span class=${`sym tone-${n.tone}`}><${w} name=${n.icon} size=${16} /><span class="verdict-word">${n.label}</span></span>
    ${a?s`<span class="small muted" data-tip=${o}>verdict${a.meta?.author?` by ${a.meta.author}`:""}${o?` \xB7 ${U(o)}`:""}</span>`:null}
  </p>`}function na({id:e,scope:t}){let n=k(Ne(e,t)).data;if(!n)return s`<h1 class="page-title title" tabindex="-1">${e}</h1><div class="skeleton late" style="block-size: 24px"></div>`;let a=n.run,o=()=>{navigator.clipboard?.writeText(a.id)};return s`
    <h1 class="page-title title" tabindex="-1"><${be} value=${a.name??a.id} label="the run's name" class="title-edit"
        onSave=${i=>Tn(a.id,t,i.trim())} />
      <${P} spec=${E("run",a.status)} word /></h1>
    ${a.error?s`<p class="bad-text" data-tip=${a.error}>${a.error.split(`
`)[0].slice(0,160)}</p>`:null}
    <div class="facts">
      <span><b>${ke(a.steps)}</b> steps</span>
      <span><b>${xe(a.duration_s)}</b></span>
      ${n.progress?s`<${sa} run=${a} progress=${n.progress} />`:null}
      <span data-tip=${a.created_at}>${U(a.created_at)}</span>
      <${ss} path=${t} />
      <${W} icon="copy" label=${`Copy the run id ${a.id}`} onClick=${o} />
      <${Je} icon="ellipsis" label="Details" title="Run details" class="run-details">
        <table class="kv small">${aa(a).map(([i,c])=>s`<tr><td class="muted">${i}</td><td>${c}</td></tr>`)}</table>
        <div class="menu-list">
          <button type="button" onClick=${()=>L(C(t,{run:a.id}),{replace:!0})}>
            <${w} name="panel-right" size=${15} /> Open in the side panel</button>
          <button type="button" onClick=${o}><${w} name="copy" size=${15} /> Copy the run id</button>
          ${a.git?.commit?s`<button type="button" onClick=${()=>navigator.clipboard?.writeText(a.git.commit)}>
            <${w} name="git-commit" size=${15} /> Copy the commit</button>`:null}
        </div>
      <//>
    </div>
    ${(n.proposals??[]).length?s`<div class="checks">
          ${n.proposals.map(i=>{let c=E("result",i.check);return s`<a class=${`check small tone-${c.tone}`} href=${C(i.group)} data-tip=${i.statement}>
              <${w} name=${c.icon} size=${14} />${i.group==="."?"own proposal":i.group}
              ${i.verdict?s`<${P} spec=${E("verdict",i.verdict)} size=${14} />`:null}</a>`})}
        </div>`:null}`}function sa({run:e,progress:t}){let{epoch:n,total:a,fraction:o,steps_per_epoch:i}=t,c=e.status==="running"&&o!==null&&i&&e.steps_per_s?xe((1-o)*a*i/e.steps_per_s):null;return s`<span>epoch <b>${n}</b>${a?` of ${a}`:""}${o===null?"":` \xB7 ${Math.round(o*100)} % through`}${c?` \xB7 about ${c} left`:""}</span>`}function ss({path:e}){let t=k(wt(e)).data?.summary;if(!t)return null;let n=Object.entries(t.config??{}).map(([i,c])=>`${ht(i)} ${F(c)}`).join(", "),a=ne(e.split("/").pop()??""),o=`${t.stat} of ${t.metric} over ${a?"the run":"all runs"}${n?` (${n})`:""}`;return s`<span data-tip=${o}>
    best <b>${t.label??ht(`metric.${t.metric}.${t.stat}`)} ${F(t.value)}</b>
    ${a?null:s` · <a href=${de(t.run)}>${t.name}</a>`}
  </span>`}function aa(e){return[["id",e.id],["host",e.host],["commit",e.git?.commit&&`${e.git.commit.slice(0,10)}${e.git.dirty?" (dirty)":""}`],["branch",e.git?.branch],["job",e.scheduler?.job_id&&`${e.scheduler.kind} ${e.scheduler.job_id}`],["attempts",e.attempts>1?String(e.attempts):null],["started",e.created_at],["ended",e.ended_at]].filter(n=>!!n[1]).map(([n,a])=>[n,String(a)])}var Mt=80;function as({node:e}){let t=J("main"),n=J(e.data?.keys?"keys":""),a=e.props.mode==="run",o=e.props.title??(a?"Config":"Hyperparameters");return s`<${ze} id=${`config:${e.id}`} title=${o} open=${e.props.open} result=${t}>
    ${t.data?a?s`<${Qe} config=${t.data.config} varying=${Ae(n.data)} />`:s`<${oa} rows=${t.data.config?.rows??[]} />`:s`<div class="skeleton late" style="block-size: 80px"></div>`}
  <//>`}function oa({rows:e}){let t=new Set(Ae({config:{rows:e}})),n=e.filter(([a])=>t.has(a.replace(/^config\./,"")));return n.length?s`<table class="kv small">${n.map(([a,,o])=>{let i=Array.isArray(o)?o.map(F).join(", "):`${F(o.min)} \u2026 ${F(o.max)} \xB7 ${o.distinct} values`;return s`<tr><td data-tip=${a}>${a.replace(/^config\./,"")}</td>
      <td data-tip=${i.length>Mt?i:void 0}>${i.length>Mt?`${i.slice(0,Mt-1)}\u2026`:i}</td></tr>`})}</table>`:s`<p class="muted small">No config differs between the runs.</p>`}var os=15e3;function rs({node:e}){let t=ee(V),n=ie(),[a,o]=Yt(),i=e.props.code,c=k(o&&i?{method:"code",params:i,scope:null}:null),[r,l]=y(null),[d,p]=y(120),[m,b]=y({error:null,warnings:[]}),f=x=>{ue&&console.error(`[block ${e.id}] ${x}`),b(u=>({...u,error:x}))},h=O(()=>{});T(()=>{if(!r)return;let x=!0;Le.n++;let u=()=>{x&&Le.n--,x=!1};h.current=u;let $=setTimeout(()=>{x&&f(`no first render within ${os/1e3} s`),u()},os);return()=>{clearTimeout($),u()}},[r]),T(()=>{let x=r?.contentWindow;if(!x||c.status!=="ready")return;let u=D=>x.postMessage(D,"*"),$=new Map,v=new cn,H=D=>{if(D.source!==x)return;let S=D.data;switch(S.type){case"hello":u({type:"init",init:{id:e.id,code:c.data.code,libs:e.props.libs??[],path:t.path,queries:e.data??{},params:e.props.params??{},theme:Xt.value,pair:We.value,colormaps:Ve.value,prefs:vt(t.path).value,names:[...t.names],colors:[...t.colors],metrics:t.metrics}});break;case"sub":if(!on.has(S.call.method)){u({type:"result",id:S.id,result:{status:"error",data:null,error:`${S.call.method} is not available in a custom block`,refreshing:!1}});break}$.get(S.id)?.(),$.set(S.id,Bt(S.call,re=>u({type:"result",id:S.id,result:re})));break;case"unsub":$.get(S.id)?.(),$.delete(S.id);break;case"navigate":S.url.startsWith("/")&&L(S.url);break;case"height":v.accept(performance.now())?p(Math.max(40,S.height)):B("its height keeps changing, so it is fixed at its last height");break;case"ready":b(re=>({...re,blank:S.blank,overflow:S.overflow})),h.current();break;case"warn":B(S.message);break;case"hover":pt.set(S.run);break;case"prefs":JSON.stringify(A.value)!==JSON.stringify(S.prefs)&&A.set(S.prefs);break;case"download":case"snapshot":S.href?rn(S.href,S.name)?performance.now()-j>1e3&&(j=performance.now(),Oe().download(S.href,S.name)):B(`a download of ${S.name} was refused: only PNG, SVG and CSV files`):B("it draws no SVG or canvas to download");break;case"figure":Oe().figure(S.spec,S.name).catch(re=>B(`the PDF failed: ${re.message}`));break;case"expand":ln(S.node)&&Oe().expand(S.node,t);break;case"error":f(S.message.replace(/blob:[^\s)]*?\/[\w-]+(?=:\d)/g,M)),h.current();break;default:break}},B=D=>{ue&&console.warn(`[block ${e.id}] ${D}`),b(S=>S.warnings.includes(D)?S:{...S,warnings:[...S.warnings,D]})},j=-1/0,A=vt(t.path),Y=pt.subscribe(D=>u({type:"hover",run:D})),R=A.subscribe(D=>u({type:"prefs",prefs:D}));return addEventListener("message",H),u({type:"ping"}),()=>{Y(),R(),removeEventListener("message",H);for(let D of $.values())D()}},[c.status,c.data?.code,r]),T(()=>{let x={type:"context",names:[...t.names],colors:[...t.colors],metrics:t.metrics};r?.contentWindow?.postMessage(x,"*")},[t.names,t.colors,t.metrics,r]),T(()=>{n&&r?.contentWindow?.postMessage({type:"theme",theme:n},"*")},[n]);let M=typeof i=="object"?i.path??i.block:String(i??"");Jt(e.id,{png:()=>r?.contentWindow?.postMessage({type:"snapshot"},"*")});let g=o&&c.status==="ready"&&!m.error;return s`<div ref=${a} class="custom-block">
    <div class="chart-head">
      <b class="chart-title">${e.props.title??""}</b>
      ${g?s`<span class="chart-tools">
            <${W} icon="download" label="Download what it draws (SVG or PNG)"
              onClick=${()=>r?.contentWindow?.postMessage({type:"snapshot"},"*")} />
            ${e.props.expanded?s`<${W} icon="x" label="Close (Esc)" onClick=${()=>Ie.set(null)} />`:s`<${W} icon="maximize" label="Expand" onClick=${()=>Oe().expand(e,t)} />`}
          </span>`:null}
    </div>
    <${se} caption=${e.props.expanded?void 0:e.props.caption} result=${c}>
      ${m.error?s`<div class="notice body error custom-error">
            <b>Custom block ${e.id} failed</b> <span class="muted">(${M})</span>
            <pre class="code">${m.error}</pre>
          </div>`:null}
      ${m.warnings.map(x=>s`<${z} kind="warning">${x}<//>`)}
      ${g?s`<div class="custom-frame" data-frame-blank=${m.blank?"1":void 0} data-frame-overflow=${m.overflow?"1":void 0}>
            <iframe key=${c.data.code} ref=${l} sandbox="allow-scripts" ...${ra()} title=${e.props.title??`Custom block ${e.id}`}
              style=${`height:${d}px`} />
          </div>`:null}
    <//>
  </div>`}function ra(){if(!!1)return{src:Ot("kit/frame.html")};let e=globalThis.__BT_FRAME__??{kit:"",css:""},t=e.css.replace(/<\/(style)/gi,"<\\/$1").replace(/@font-face\s*\{[^}]*\}/g,""),n=e.kit.replace(/<\/(script)/gi,"<\\/$1");return{srcdoc:`<!doctype html><html lang="en"><head><meta charset="utf-8"><style>${t}</style></head><body class="kit-frame body"><div id="root"></div><script>${n}<\/script></body></html>`}}function is({node:e}){let t=J("main"),n=ee(V),a=t.data?.entries??[];return s`<${se} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!a.length?s`<${z}>No images logged.<//>`:null}
    <div class="images">
      ${a.map(o=>s`<figure key=${`${o.run}/${o.path}`}>
          <img src=${zt(Pe(o.run,n.path),o.path)} alt=${o.caption??e.props.title} loading=${Re?"eager":"lazy"} />
          <figcaption class="small">step ${ke(o.step)}${o.caption?` \xB7 ${o.caption}`:""}</figcaption>
        </figure>`)}
    </div>
  <//>`}function ls({node:e}){let t=J("main"),n=t.data?.entries??[];return s`<${se} title=${e.props.title} caption=${e.props.caption} result=${t}>
    ${t.data&&!n.length?s`<${z}>No text logged.<//>`:null}
    ${n.map(a=>s`<div class="text-entry" key=${`${a.run}/${a.step}`}>
        <div class="muted small">step ${ke(a.step)}${a.caption?` \xB7 ${a.caption}`:""}</div>
        <pre class="code">${a.text??""}</pre>
      </div>`)}
  <//>`}function cs({node:e}){let n=`section.${ee(V).path}:${e.id}`,[a,o]=y(()=>Re||he(n,e.props.open!==!1)),i=()=>{ge(n,!a),o(!a)},c=s`${(e.children??[]).map(d=>s`<${oe} key=${d.id} node=${d} />`)}`,r=ee(Ye);if(!e.props.title)return s`<div class="stack">${c}</div>`;let l=r===e.props.title.toLowerCase();return s`<div class="view-section">
    <button type="button" class="view-section-title heading" aria-expanded=${a} aria-label=${l?`${a?"Close":"Open"} ${e.props.title}`:void 0}
        data-tip=${l?`${a?"Close":"Open"} ${e.props.title}`:void 0}
        onClick=${i}>
      <${w} name=${a?"chevron-down":"chevron-right"} size=${16} />${l?null:e.props.title}
    </button>
    ${a?s`<div class="stack">${c}</div>`:null}
  </div>`}function ds({node:e}){let t=(e.children??[]).every(n=>n.block==="stat");return s`<div class=${t?"stats":"row"}>
    ${(e.children??[]).map(n=>s`<${oe} key=${n.id} node=${n} />`)}
  </div>`}function Dt({node:e,after:t}){let n=ee(V),a=He(n.path),o=e.props.min_width??320,i=e.props.columns,c=i?`grid-template-columns: repeat(${i}, minmax(0, 1fr))`:`grid-template-columns: repeat(auto-fill, minmax(min(${o}px, 100%), 1fr))`,r=e.children??[],l=r.filter(m=>a.removed.includes(m.id)).map(m=>m.id),d=an(r.filter(m=>!l.includes(m.id)),a.order[e.id]),p=(m,b)=>{let f=d.map(h=>h.id).filter(h=>h!==m);f.splice(f.indexOf(b),0,m),nn(n.path,e.id,f)};return s`<div class="grid" style=${c}>
    ${d.map(m=>s`<${ia} key=${m.id} node=${m} path=${n.path} span=${a.spans[m.id]??m.props.span??1}
      columns=${i} onDrop=${b=>b!==m.id&&p(b,m.id)} />`)}
    ${t??null}
    ${l.length?s`<div class="grid-note"><button type="button" class="link small" onClick=${()=>bt(n.path,l)}>${l.length} hidden · show</button></div>`:null}
  </div>`}var Nt=[1,2,"full"];function ia(e){let[t,n]=y(!1),a=Nt[(Nt.indexOf(e.span)+1)%Nt.length],o=i=>i==="full"?"full width":`${i} column${i===1?"":"s"}`;return s`<div class=${`cell span-${e.span}${t?" drop":""}`}
      onDragOver=${i=>{i.preventDefault(),n(!0)}}
      onDragLeave=${()=>n(!1)}
      onDrop=${i=>{i.preventDefault(),n(!1),e.onDrop(i.dataTransfer?.getData("text/x-block")??"")}}>
    <div class="cell-tools">
      <span class="cell-handle" draggable="true" role="button" tabindex="-1" aria-label="Drag to move"
        data-tip="Drag to move" onDragStart=${i=>i.dataTransfer?.setData("text/x-block",e.node.id)}>
        <${w} name="grip" size=${14} /></span>
      <button type="button" class="cell-width small" data-tip=${`Width: ${o(e.span)}; click for ${o(a)}`}
        aria-label=${`Width ${o(e.span)}`} onClick=${()=>sn(e.path,e.node.id,a)}>
        ${e.span==="full"?"\u2194":e.span}</button>
    </div>
    <${oe} node=${{...e.node,props:{...e.node.props,span:1}}} />
  </div>`}function us({root:e}){let t=ee(V),n=He(t.path),a=k({method:"keys",params:{from:t.path},scope:t.path}).data,o=e.props.template;if(!o||!1)return null;let i=new Set(n.removed),c=new Set([...t.charted].filter(([f])=>!i.has(f)).flatMap(([,f])=>f)),r=n.added.filter(f=>!c.has(f)).map(f=>({block:"line",id:`added-${f}`,props:{y:f},data:{main:{...o,params:{...o.params,y:[f]}}}})),l=new Set([...c,...r.filter(f=>!i.has(f.id)).map(f=>f.props.y)]),d=(a?.metrics?.rows??[]).map(f=>f[0]).filter(f=>!l.has(f));if(!a||!(d.length||r.length))return null;let p=f=>[...t.charted].find(([h,M])=>i.has(h)&&M.includes(f))?.[0]??r.find(h=>i.has(h.id)&&h.props.y===f)?.id,m=f=>{let h=p(f);h?bt(t.path,[h]):et(t.path,M=>({added:[...M.added,f]}))},b=d.length?s`<div class="add-chart">
        <span class="add-chart-label"><${w} name="plus" size=${16} /> Add a chart</span>
        <${Ze} single options=${d} value=${[]} label="Metric for a new chart" placeholder="Search metrics"
          onChange=${([f])=>m(f)} />
      </div>`:null;return s`<${I}><${Dt} node=${{block:"grid",id:"added",props:{},children:r}} after=${b} /><//>`}function ms({node:e}){let t=e.children??[],n=()=>new URLSearchParams(location.hash.slice(1)).get("tab"),[a,o]=y(()=>t.find(r=>r.id===n())?.id??t[0]?.id),i=r=>{history.replaceState(history.state,"",`${location.pathname}${location.search}#tab=${encodeURIComponent(r)}`),o(r)},c=t.find(r=>r.id===a)??t[0];return Re?s`<div class="stack">${t.map(r=>s`<${oe} key=${r.id} node=${r} />`)}</div>`:s`<div class="tabs">
    <div class="tab-list heading" role="tablist" aria-label=${e.props.title??"Tabs"}>
      ${t.map(r=>s`<button type="button" role="tab" id=${`tab-${r.id}`} aria-selected=${r.id===c?.id}
          aria-controls=${`panel-${r.id}`} onClick=${()=>i(r.id)}>${r.props.title??r.id}</button>`)}
    </div>
    ${c?s`<div class="stack" role="tabpanel" id=${`panel-${c.id}`} aria-labelledby=${`tab-${c.id}`}>
          ${(c.children??[]).map(r=>s`<${oe} key=${r.id} node=${r} />`)}
        </div>`:null}
  </div>`}var la={section:cs,row:ds,grid:Dt,line:hn,table:wn,stat:yn,images:is,text:ls,proposal:Vn,note:es,output:Zn,config:as,memory:Wn,groups:qn,notes:Xn,tabs:ms,scatter:gn,bar:vn,histogram:bn,data_table:mn,timeline:pn,custom:rs,markdown:Qn};function oe({node:e}){return s`<${en} node=${e} blocks=${la} />`}function ps(e,t){let n=e.split(`
`),a=t.split(`
`),o=n.length,i=a.length,c=Array.from({length:o+1},()=>new Uint32Array(i+1));for(let p=o-1;p>=0;p--)for(let m=i-1;m>=0;m--)c[p][m]=n[p]===a[m]?c[p+1][m+1]+1:Math.max(c[p+1][m],c[p][m+1]);let r=[],l=0,d=0;for(;l<o&&d<i;)n[l]===a[d]?(r.push({kind:"same",text:n[l]}),l++,d++):c[l+1][d]>=c[l][d+1]?r.push({kind:"removed",text:n[l++]}):r.push({kind:"added",text:a[d++]});for(;l<o;)r.push({kind:"removed",text:n[l++]});for(;d<i;)r.push({kind:"added",text:a[d++]});return r}function $s(e,t=3){let n=[],a=0;for(;a<e.length;){if(e[a].kind!=="same"){n.push(e[a++]);continue}let o=a;for(;o<e.length&&e[o].kind==="same";)o++;let i=a===0?0:t,c=o===e.length?0:t;o-a>i+c+1?n.push(...e.slice(a,a+i),{kind:"skip",count:o-a-i-c},...e.slice(o-c,o)):n.push(...e.slice(a,o)),a=o}return n}var _t={stat:"readings",line:"charts",scatter:"charts",bar:"charts",histogram:"charts",table:"runs",data_table:"table",images:"images",text:"text",markdown:"text",note:"note",notes:"notes",memory:"memory",groups:"groups",output:"output",config:"config",timeline:"timeline",proposal:"predictions"};function fs(e){if(_t[e.block])return _t[e.block];if(e.block==="row"||e.block==="grid"){let n=new Set((e.children??[]).map(o=>_t[o.block])),[a]=n;if(n.size===1&&a)return a}let t=String(e.props.title??"").trim();return t&&t.split(/\s+/).length<=2?t.toLowerCase():""}function dt(e){let t=k(Ke(e.path)),n=ie(),a=_(t.data),o=_e(()=>Xe(a.map(p=>p["run.id"]),n),[t.data,n]),i=_e(()=>new Map(a.map(p=>[p["run.id"],p["run.name"]??p["run.id"]])),[t.data]),c=e.plain?"view plain":"sections view";if(!e.view)return s`<div class=${c}>${e.before}
      ${e.plain?s`<div class="skeleton late" style="block-size: 320px"></div>`:s`<${I} label="view"><div class="skeleton late" style="block-size: 320px"></div><//>`}
    </div>`;let r=e.view.view,l={path:e.path,colors:o,names:i,metrics:e.view.metrics??{},charted:hs(r)};if(e.plain)return s`<div class=${c}><${V.Provider} value=${l}><${oe} node=${r} /><//></div>`;let d=r.block==="section"&&!r.props.title?r.children??[]:[r];return s`<div class=${c}>${e.before}
    <${V.Provider} value=${l}>
      ${d.map(p=>{let m=fs(p);return s`<${I} key=${p.id} label=${m}><${Ye.Provider} value=${m}><${oe} node=${p} /><//><//>`})}
      <${us} root=${r} />
    <//>
  </div>`}function hs(e,t=new Map){e.block==="line"&&t.set(e.id,e.data?.main?.params?.y??[]);for(let n of e.children??[])hs(n,t);return t}function gs(e){if(null)return s`<div class="view-source small"><${w} name="clock" size=${14} />
    <span>a snapshot of <b>${e.path==="."?"the log dir":e.path}</b>, taken ${new Date(null.taken*1e3).toLocaleString()};
      curves at ${null.points==="all"?"every logged point":`${null.points} points`}; Beamtime ${null.version}</span></div>`;let t=e.view,n=N(q),a=n.page==="group"&&n.version,o=t.versions?s`<a href=${C(e.path,{history:!0})}><${w} name="history" size=${14} /> history (${t.versions})</a>`:null,i;switch(t.source){case"draft":i=s`draft <b>${t.draft}</b>`;break;case"view":i=s`${t.title?s`<em>${t.title}</em> · `:null}saved ${U(ve(t.version))} by ${t.author??"unknown"}`;break;default:i=s`the built-in view`}return s`<div class="view-source small">
    <${w} name="layout" size=${14} /><span>${i}</span>
    ${a?s`<a href=${C(e.path)}>an older version · show the current one</a>`:null}
    ${o}
    ${t.outdated?.length&&!a?s`<${ca} path=${e.path} outdated=${t.outdated} />`:null}
    ${t.source==="draft"||a?null:s`<${da} path=${e.path} />
        <${ua} path=${e.path} view=${t} />`}
  </div>`}function ca(e){let[t,n]=y(null),a=e.outdated.map(i=>i.name).join(", ");return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{await Mn(e.path)}catch(i){n(i.message.split(`
`)[0])}}}
      data-tip=${`A newer version of ${a} exists; update re-pins this view to it (a new version)`}>
      <${w} name="update" size=${14} /> update ${a}</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function da(e){let[t,n]=y(null);return s`<button type="button" class="link small" onClick=${async()=>{n(null);try{Te.set(await nt(e.path,null,""))}catch(o){n(o.message)}}} data-tip="Add a text panel at the top of this page's view">
      <${w} name="file-text" size=${14} /> add text</button>
    ${t?s`<span class="bad-text small">${t}</span>`:null}`}function ua(e){let t=He(e.path),n=tn(t),[a,o]=y(!1),[i,c]=y(e.view.title??""),[r,l]=y(e.view.finding??""),[d,p]=y(null),[m,b]=y(!1);if(!n&&!a)return null;let f=async h=>{h.preventDefault(),b(!0),p(null);try{let M={charts:t.charts,view:t.view,added:t.added,removed:t.removed,order:t.order,spans:t.spans};await K("save_view",{path:e.path,prefs:M,title:i,finding:r}),et(e.path,()=>({view:{},charts:{},added:[],removed:[],order:{},spans:{}})),Ce(g=>["view","view_history","summary"].includes(g.method)&&g.scope===e.path),o(!1)}catch(M){p(M.message)}finally{b(!1)}};return a?s`<form class="save-form" onSubmit=${f}>
    <${Be} label="Title"><input value=${i} onInput=${h=>c(h.target.value)} /><//>
    <${Be} label="Finding"><input value=${r} placeholder="the key result in one sentence"
        onInput=${h=>l(h.target.value)} /><//>
    <div class="save-actions">
      <${ae} type="submit" icon=${m?"hourglass":"save"} disabled=${m}>${m?"Saving\u2026":"Save as view"}<//>
      <${ae} icon="x" kind="quiet" onClick=${()=>o(!1)}>Cancel<//>
      ${d?s`<span class="bad-text small">${d}</span>`:null}
    </div>
  </form>`:s`<${ae} icon="save" class="save-view" onClick=${()=>o(!0)}
        tip="Save your chart settings and added charts as this page's view, for everyone">Save as view<//>`}function vs(e){let t=k(On(e.path)),n=t.data?.entries??[],[a,o]=y(null),i=a??n.slice(0,2).map(r=>r.version).reverse(),c=r=>{let l=i.includes(r)?i.filter(d=>d!==r):[...i,r].slice(-2);o(l.sort())};return t.status==="error"?s`<${z} kind="error">${t.error}<//>`:s`<section class="history">
    <h2 class="history-title heading"><${w} name="history" size=${16} /> View history</h2>
    ${t.data&&!n.length?s`<${z}>No saved view yet; the page shows the built-in view.<//>`:null}
    <ol class="versions">
      ${n.map((r,l)=>s`<li key=${r.version} class=${i.includes(r.version)?"picked":""}>
          <label><input type="checkbox" checked=${i.includes(r.version)} onChange=${()=>c(r.version)} />
            <span class="num muted" data-tip=${r.version}>${U(r.time)}</span>
            <b>${r.title??"untitled"}</b><span class="muted">${r.author??""}</span>
            ${r.message?s`<span>${r.message}</span>`:null}</label>
          <a href=${l===0?C(e.path):C(e.path,{version:r.version})}
            onClick=${d=>{d.preventDefault(),L(l===0?C(e.path):C(e.path,{version:r.version}))}}>${l===0?"current":"show"}</a>
        </li>`)}
    </ol>
    ${i.length===2?s`<${ma} path=${e.path} a=${i[0]} b=${i[1]} />`:null}
  </section>`}function ma(e){let t=r=>({method:"view_show",params:{group:e.path,version:r},scope:e.path}),n=k(t(e.a)).data,a=k(t(e.b)).data,o=k(pe(e.path,e.a)).data,i=k(pe(e.path,e.b)).data,c=n&&a?$s(ps(n.yaml,a.yaml)):[];return s`<div class="compare">
    <h3 class="block-title heading">Changes from ${U(ve(e.a))} to ${U(ve(e.b))}</h3>
    <pre class="diff code">${c.map(r=>r.kind==="skip"?s`<div class="diff-skip">⋯ ${r.count} unchanged lines</div>`:s`<div class=${`diff-${r.kind}`}>${r.kind==="added"?"+ ":r.kind==="removed"?"\u2212 ":"  "}${r.text}</div>`)}</pre>
    <div class="side-by-side">
      <div><h3 class="block-title heading">${o?.title??e.a}</h3><${dt} path=${e.path} view=${o} plain /></div>
      <div><h3 class="block-title heading">${i?.title??e.b}</h3><${dt} path=${e.path} view=${i} plain /></div>
    </div>
  </div>`}function bs(e){return zn(e.path),e.history?s`<div class="page"><div class="sections">
      <${I} label=${ys(e.path)}><${Tt} path=${e.path} /><//>
      <${I} label="history"><${vs} path=${e.path} /><//>
    </div></div>`:s`<div class="page">
    <${pa} path=${e.path} version=${e.version??null} draft=${e.draft??null} />
  </div>`}function pa(e){let t=k(pe(e.path,e.version,e.draft));T(()=>{t.status==="ready"&&requestAnimationFrame(Ft)},[t.status==="ready"]);let n=s`
    <${I} label=${ys(e.path)}>
      <${Tt} path=${e.path} finding=${t.data?.finding} />
      ${t.data?s`<${gs} path=${e.path} view=${t.data} />`:null}
    <//>
    ${ne(e.path.split("/").pop()??"")?null:s`<${ns} path=${e.path} />`}`;return t.status==="error"?s`<div class="sections">${n}
      <${I} label="view">
        ${$a(e.path,t.error)?s`<${z} kind="warning">${t.error} The page fills in once the remote answers again.<//>`:s`<${z} kind="error">${t.error}<//>`}
      <//>
    </div>`:s`<${dt} path=${e.path} view=${t.data} before=${n} />`}function ys(e){return ne(e.split("/").pop()??"")?"run":"group"}function $a(e,t){return e.startsWith("@")&&/is unreachable since/.test(t??"")}function ws(e){T(()=>{Se(pe(e.id)).then(n=>L(C(n.path),{replace:!0})).catch(()=>{})},[e.id]);let t=k(pe(e.id));return t.status==="error"?s`<div class="page"><${z} kind="error">${t.error}<//></div>`:s`<div class="page"><div class="skeleton late" style="block-size: 320px"></div></div>`}var fa={running:"accent",finished:"good",failed:"bad",killed:"warn",lost:"muted"},Lt=20,De=-1,ha=[["day",86400],["week",7*86400],["month",30*86400]];function xs(e){let t=_(k(le()).data).map(r=>r.path),n=k({method:"runs",params:{from:e.from,select:["run.name","run.status","run.group","run.created_at","run.ended_at"],sort:["run.created_at"],limit:2e3},scope:e.from}),a=k({method:"notes",params:{from:e.from,limit:500,current:!0},scope:e.from});Fe("Timeline",_(n.data).filter(r=>r["run.status"]==="running").length);let o=Date.now()/1e3,i=_(n.data).filter(r=>r["run.created_at"]).map((r,l)=>({id:r["run.id"],name:r["run.name"]??r["run.id"],group:r["run.group"],status:r["run.status"],start:Date.parse(r["run.created_at"])/1e3,end:r["run.ended_at"]?Date.parse(r["run.ended_at"])/1e3:o,lane:l})),c=(a.data?.entries??[]).map(r=>({id:r.id,type:r.type,group:r.group,description:r.description,t:Date.parse(ve(r.id))/1e3}));return s`<div class="page timeline-page"><div class="sections">
    <${I} label="timeline"><header class="header">
      <h1 class="page-title title" tabindex="-1">Timeline</h1>
      <div class="timeline-filter">
        <${Be} label="Group" inline>
          <select value=${e.from} onChange=${r=>L(Ge(r.target.value),{replace:!0})}>
            ${t.map(r=>s`<option value=${r}>${r==="."?"everything":r}</option>`)}
          </select><//>
        <span class="muted small">${i.length} runs · ${c.length} notes · wheel zooms, drag pans, click opens</span>
      </div>
    </header><//>
    <${I} label="runs">
      ${n.status==="error"?s`<${z} kind="error">${n.error}<//>`:null}
      ${n.data&&a.data?s`<${ga} bars=${i} marks=${c} />`:s`<div class="skeleton late" style="block-size: 320px"></div>`}
    <//>
  </div></div>`}function ga(e){let t=ie(),n=O(null),a=[...e.bars.flatMap(g=>[g.start,g.end]),...e.marks.map(g=>g.t)],o=a.length?ks(Math.min(...a),Math.max(...a)):ks(Date.now()/1e3-86400,Date.now()/1e3),[i,c]=y(o),r=e.bars.length,l=Math.min(900,Math.max(160,(r+1.5)*Lt+40)),p=$n(n,fn,t?(g=>{let x=dn(i[0],i[1]),u=v=>g.colors[fa[v]??"muted"],$=v=>g.colors[v==="verdict"?"good":v==="decision"?"accent":v==="question"?"warn":"muted"];return{style:qt(g),height:l,x:{range:i,log:!1,format:v=>un(v,x.step),label:"",splits:x.at},y:{range:[De-.8,r+.5],log:!1,reverse:!0,label:"",size:150,splits:r<=40?[De,...e.bars.map(v=>v.lane)]:[De],format:v=>v===De?"notes":ka(e.bars[Math.round(v)]?.name??"")},draw:({ctx:v,x:H,y:B,px:j,focused:A})=>{let Y=Lt*.62*j;for(let R of e.bars){let D=H(R.start),S=Math.max(3*j,H(R.end)-D);v.fillStyle=A!==null&&A!==R.id?Wt(u(R.status),.35):u(R.status),v.beginPath(),v.roundRect(D,B(R.lane)-Y/2,S,Y,3*j),v.fill()}for(let R of e.marks){let D=H(R.t),S=B(De),re=(A===R.id?6:4.5)*j;v.fillStyle=$(R.type),v.beginPath(),v.moveTo(D,S-re),v.lineTo(D+re,S),v.lineTo(D,S+re),v.lineTo(D-re,S),v.closePath(),v.fill()}},hit:(v,H,B,j)=>{if(Math.abs(H-j(De))<Lt/2){let R=wa(e.marks,D=>Math.abs(B(D.t)-v),8);return R?{key:R.id,rows:ba(R)}:null}let A=Math.round((H-j(0))/(j(1)-j(0))),Y=e.bars.find(R=>R.lane===A&&B(R.start)-3<=v&&v<=Math.max(B(R.end),B(R.start)+3)+3);return Y?{key:Y.id,rows:va(Y)}:null},onClick:v=>{let H=e.marks.find(B=>B.id===v);H?L(C(H.group,{drawer:!0})):L(de(v))}}})(t):null,[i,e.bars,e.marks],t),m=g=>{if(!p.current)return;g.preventDefault();let x=p.current.xAt(g.clientX),u=Math.exp(g.deltaY*.0015);c(([$,v])=>Pt([x-(x-$)*u,x+(v-x)*u],o))},b=O(null),f=g=>b.current={x:g.clientX,range:i},h=g=>{if(!b.current||!p.current||!(g.buttons&1))return;let x=(g.clientX-b.current.x)*p.current.xPerPixel(),[u,$]=b.current.range;Math.abs(g.clientX-b.current.x)>3&&c(Pt([u-x,$-x],o))},M=Math.max(...a,Date.now()/1e3);return s`<div class="timeline-chart">
    <div class="segmented small" role="radiogroup" aria-label="Range">
      ${ha.map(([g,x])=>s`<button type="button" role="radio" aria-checked=${Math.abs(i[1]-i[0]-x)<1}
          onClick=${()=>c(Pt([M-x,M+x*.02],[Math.min(o[0],M-x),o[1]]))}>last ${g}</button>`)}
      <button type="button" role="radio" aria-checked=${i[0]===o[0]&&i[1]===o[1]} onClick=${()=>c(o)}>all</button>
    </div>
    <div class="chart-plot" ref=${n} style=${`min-block-size:${l}px`}
      onWheel=${m} onPointerDown=${f} onPointerMove=${h} onPointerUp=${()=>b.current=null}></div>
    <p class="muted small">${ya(t)}</p>
  </div>`}function va(e){return[{label:e.name,value:"",color:null,strong:!0},{label:"group",value:e.group,color:null},{label:"status",value:e.status,color:null},{label:"started",value:U(new Date(e.start*1e3).toISOString()),color:null},{label:"duration",value:xe(e.end-e.start),color:null}]}function ba(e){return[{label:e.description.slice(0,80),value:"",color:null,strong:!0},{label:e.type,value:e.group,color:null},{label:"written",value:U(new Date(e.t*1e3).toISOString()),color:null}]}function ya(e){return e?"bars: runs by status \xB7 diamonds: notes (green verdicts, blue decisions, amber questions)":""}function wa(e,t,n){let a=null,o=n;for(let i of e){let c=t(i);c<o&&([a,o]=[i,c])}return a}function ks(e,t){let n=Math.max(60,(t-e)*.03);return[e-n,t+n]}function Pt([e,t],n){let a=Math.min(n[1]-n[0],Math.max(60,t-e)),o=Math.max(n[0],Math.min(e,n[1]-a));return[o,o+a]}function ka(e){return e.length>22?`${e.slice(0,21)}\u2026`:e}function Ss(){let e=N(Ie),t=O(null);if(T(()=>{let o=t.current;if(!o||!e)return;o.showModal();let i=()=>Ie.set(null);return o.addEventListener("close",i),()=>o.removeEventListener("close",i)},[e]),!e)return null;let n={...e.node,props:{...e.node.props,expanded:!0}},a=String(n.props.title??n.props.y??"Chart");return s`<dialog class="sheet wide chart-dialog" ref=${t} aria-label=${a} closedby="any">
    <${V.Provider} value=${e.view}><${oe} node=${n} /><//>
  </dialog>`}function Cs(e,t){let n=e.toLowerCase(),a=t.toLowerCase();if(!n)return 1;let o=a.indexOf(n);if(o>=0)return 100-Math.min(o,50)-a.length/100;let i=0,c=0;for(let r of a)if(r===n[i]?i++:i>0&&c++,i===n.length)return 40-Math.min(c,39);return 0}function Ts(e){let[t,n]=y(e.query),[a,o]=y(0),i=O(null),c=_(k(le()).data),r=_(k(at()).data);T(()=>{let u=i.current;u.showModal();let $=()=>Q.set(null);u.addEventListener("close",$);let v=!1,H=A=>{let Y=u.getBoundingClientRect();return A.clientX<Y.left||A.clientX>Y.right||A.clientY<Y.top||A.clientY>Y.bottom},B=A=>v=H(A),j=A=>v&&H(A)&&u.close();return"closedBy"in HTMLDialogElement.prototype||(u.addEventListener("pointerdown",B),u.addEventListener("pointerup",j)),()=>{u.removeEventListener("close",$),u.removeEventListener("pointerdown",B),u.removeEventListener("pointerup",j)}},[]);let l=()=>i.current?.close(),d=u=>()=>L(u),p=q.value,m=p.page==="group"?p.path:".",b=(u,$,v,H)=>({section:"Commands",label:u,detail:$,sym:{icon:v,tone:"muted",label:u},run:H}),h=[...c.map(u=>({section:"Groups",label:u.path==="."?"local":u.path,detail:`${u.runs} runs${u.proposal?` \xB7 ${u.proposal}`:""}`,sym:E("research",u.status),run:d(C(u.path))})),...r.map(u=>({section:"Runs",label:u["run.name"]??u["run.id"],detail:`${u["run.status"]} \xB7 ${u["run.path"]}`,sym:E("run",u["run.status"]),run:d(C(u["run.path"]))})),b("Theme: light","","sun",()=>qe("light")),b("Theme: dark","","moon",()=>qe("dark")),b("Theme: follow the system","","monitor",()=>qe("system")),b("Copy link to this page","","link",()=>{navigator.clipboard?.writeText(location.href)}),b("Show notes and timeline","i","file-text",d(C(m,{drawer:!0}))),b("Show or hide the sidebar","\u2318B","panel-left",()=>Z.set(!Z.value)),b(te.value?"Resume live updates":"Pause live updates","p",te.value?"play":"pause",()=>te.set(!te.value)),b("Keyboard shortcuts","?","keyboard",()=>$e.set(!0)),b("Settings","","settings",d("/settings/appearance"))].map(u=>({it:u,s:Math.max(Cs(t,u.label),Cs(t,u.detail)*.5)})).filter(u=>u.s>0).sort((u,$)=>$.s-u.s||Es(u.it.section)-Es($.it.section)).slice(0,60).map(u=>u.it),M=u=>{u&&(l(),u.run())},g=u=>{if(u.key==="ArrowDown")o(Math.min(h.length-1,a+1));else if(u.key==="ArrowUp")o(Math.max(0,a-1));else if(u.key==="Enter")M(h[a]);else return;u.preventDefault()},x="";return s`<dialog class="sheet" ref=${i} aria-label="Search" closedby="any">
    <div class="palette-input"><${w} name="search" size=${16} />
      <input class="body" autofocus value=${t} placeholder="Groups, runs by name, id or status, commands" aria-label="Search"
        aria-controls="palette-list" aria-activedescendant=${h[a]?`pal-${a}`:void 0}
        onInput=${u=>{n(u.target.value),o(0)}} onKeyDown=${g} />
    </div>
    <ul class="palette-list" id="palette-list" role="listbox">
      ${h.map((u,$)=>{let v=u.section!==x&&!t?x=u.section:null;return s`${v?s`<li class="palette-head small" role="presentation">${v}</li>`:null}
          <li id=${`pal-${$}`} class="item" role="option" aria-selected=${$===a}
              onMouseMove=${()=>o($)} onClick=${()=>M(u)}>
            <${P} spec=${u.sym} /><span class="label">${u.label}</span><span class="detail small">${u.detail}</span>
          </li>`})}
    </ul>
  </dialog>`}function Es(e){return["Groups","Runs","Commands"].indexOf(e)}function ut(e,t=[]){let n=new Map,a=(r,l={})=>({path:r,name:r==="."?"local":r.split("/").pop(),runs:l.runs??0,running:l.running??0,failed:(l.failed??0)+(l.killed??0)+(l.lost??0),status:l.status??null,children:[]});for(let r of e)n.set(r.path,a(r.path,r));(t.length===0||t.some(r=>r.name==="local"))&&!n.has(".")&&n.set(".",a("."));for(let r of t){let l=r.name==="local"?".":r.name;n.has(l)||n.set(l,a(l)),Object.assign(n.get(l),{state:r.state,error:r.error})}for(let r of n.values()){if(G(r.path))continue;let l=r.path.lastIndexOf("/"),d=l<0?".":r.path.slice(0,l);(n.get(d)??n.get(we(r.path))??n.get(".")).children.push(r)}for(let r of n.values())r.children.sort((l,d)=>l.name.localeCompare(d.name));let i=[...n.values()].filter(r=>r.path!=="."&&G(r.path)).sort((r,l)=>r.name.localeCompare(l.name)),c=n.get(".");return c?[c,...i]:i}function Ms(e,t,n,a=new Set){let o=[],i=n.toLowerCase(),c=r=>{(!i||r.path.toLowerCase().includes(i)||Ns(r,i))&&(o.push(r),(i||(G(r.path)?!a.has(r.path):t.has(r.path)))&&r.children.forEach(c))};return e.forEach(c),o}function Ns(e,t){return e.children.some(n=>n.path.toLowerCase().includes(t)||Ns(n,t))}function Ds(e,t){if(G(t))return e;let n=t.lastIndexOf("/"),a=n<0?".":t.slice(0,n),o=i=>i.path===a?i:i.children.map(o).find(c=>c)??null;return e.map(o).find(i=>i)?.children??[]}function _s(e){return G(e)?0:e.split("/").length-(e.startsWith("@")?1:0)}function Ls(){let e=N(q),t=k(le()),[n,a]=y(()=>new Set(he("open",[]))),[o,i]=y(()=>new Set(he("closed-hosts",[]))),[c,r]=y(""),l=O(null),d=e.page==="group"?e.path:null,p=ut(_(t.data),t.data?.meta?.sources??[]),m=Ms(p,Ca(n,d),c,o),b=g=>G(g)?!o.has(g):n.has(g),f=(g,x)=>{let u=x??!b(g);if(G(g)){let v=new Set(o);u?v.delete(g):v.add(g),ge("closed-hosts",[...v]),i(v);return}let $=new Set(n);u?$.add(g):$.delete(g),ge("open",[...$]),a($)},h=O(d);return T(()=>{d!==h.current&&d&&!G(d)&&o.has(we(d))&&f(we(d),!0),h.current=d},[d]),s`<nav class="sidebar" aria-label="Groups">
    <label class="filter input body"><${w} name="search" size=${14} />
      <input type="search" placeholder="Filter groups" value=${c} aria-label="Filter groups"
        onInput=${g=>r(g.target.value)} />
    </label>
    <div class="tree" ref=${l} onKeyDown=${g=>{let x=[...l.current?.querySelectorAll("a.tree-item")??[]],u=x.indexOf(document.activeElement),$=m[u];switch(g.key){case"ArrowDown":x[Math.min(x.length-1,u+1)]?.focus();break;case"ArrowUp":x[Math.max(0,u-1)]?.focus();break;case"ArrowRight":$?.children.length&&f($.path,!0);break;case"ArrowLeft":$?.children.length&&b($.path)?f($.path,!1):$&&x[m.findIndex(v=>v.path===Sa($.path))]?.focus();break;default:return}g.preventDefault()}} role="tree">
      ${m.map(g=>s`<${xa} key=${g.path} node=${g} current=${g.path===d}
        open=${b(g.path)||!!c} onToggle=${()=>f(g.path)} />`)}
    </div>
  </nav>`}function xa(e){let t=e.node,n=()=>Ue(t.path),a=t.children.length>0,o=t.state==="unreachable";return s`<a class=${`tree-item${e.current?" current":""}${G(t.path)?" source-root":""}`} href=${C(t.path)}
      role="treeitem" aria-current=${e.current?"page":void 0} aria-expanded=${a?e.open:void 0}
      style=${`padding-inline-start:${8+_s(t.path)*14}px`} onMouseEnter=${n} onFocus=${n}
      onClick=${i=>{i.metaKey||i.ctrlKey||(i.preventDefault(),L(C(t.path)))}}>
    <span class="twisty" onClick=${i=>{i.preventDefault(),i.stopPropagation(),e.onToggle()}}>
      ${a?s`<${w} name=${e.open?"chevron-down":"chevron-right"} size=${14} />`:null}</span>
    ${G(t.path)?s`<${P} size=${14} spec=${{icon:o?"cloud-off":"server",tone:"muted",label:o?`Unreachable: ${t.error??"no answer"}`:t.path==="."?"This machine":`Remote host ${t.name}`}} />`:null}
    <span class="tree-name">${t.name}</span>
    <span class="tree-marks">
      ${t.running?s`<${P} spec=${E("run","running")} size=${14} />`:null}
      ${t.failed?s`<${P} spec=${{...E("run","failed"),label:`${t.failed} failed, killed or lost`}} size=${14} />`:null}
    </span>
    <span class="count small">${t.runs||""}</span>
  </a>`}function Sa(e){if(G(e))return e;let t=e.lastIndexOf("/");return t<0?".":e.slice(0,t)}function Ca(e,t){if(!t||t===".")return e;let n=new Set(e),a=t.split("/");for(let o=1;o<a.length;o++)n.add(a.slice(0,o).join("/"));return n}function Rs(){let e=N(q),t=N(Z),n=N(Q),a=N($e),o=O(null);T(()=>Ut(()=>o.current),[]),T(()=>(addEventListener("keydown",Ps),()=>removeEventListener("keydown",Ps)),[]);let i=e.page==="group"&&e.drawer,c;switch(e.page){case"group":c=s`<${bs} key=${`${e.path} ${e.version} ${e.draft} ${e.history}`} path=${e.path} version=${e.version}
        draft=${e.draft} history=${e.history} />`;break;case"run":c=s`<${ws} id=${e.id} />`;break;case"settings":c=s`<${Kn} />`;break;case"timeline":c=s`<${xs} key=${e.from} from=${e.from} />`;break;default:c=s`<div class="page"><p>No page at ${e.url}. <a href="/f/local">Go to the log dir.</a></p></div>`}return ue||!1?s`<main class="main render-main" ref=${o}>${c}</main>`:s`<div class=${`shell${t?"":" no-sidebar"}${i?" with-drawer":""}`}>
    <${Fn} />
    ${t?s`<${Ls} />`:null}
    <main class="main" ref=${o}>${c}</main>
    ${i?s`<${ts} path=${e.path} run=${e.run} />`:null}
    <${jn} />
    ${n!==null?s`<${Ts} query=${n} />`:null}
    ${a?s`<${Ta} />`:null}
    <${Ss} />
  </div>`}function Ps(e){let t=e.metaKey||e.ctrlKey;if(t&&e.key.toLowerCase()==="k"){e.preventDefault(),Q.set(Q.value===null?"":null);return}if(t&&e.key.toLowerCase()==="b"){e.preventDefault(),Z.set(!Z.value);return}if(e.key==="Escape"){if(Q.value!==null||$e.value)return;let a=q.value;return a.page==="group"&&a.run?L(C(a.path,{drawer:!0}),{replace:!0}):a.page==="group"&&a.drawer?L(C(a.path),{replace:!0}):void 0}if(t||e.altKey||An(e)||Q.value!==null||$e.value)return;let n=q.value;switch(e.key){case"/":e.preventDefault(),Q.set("");break;case"?":$e.set(!$e.value);break;case"p":te.set(!te.value);break;case"i":n.page==="group"&&L(C(n.path,{drawer:!n.drawer}),{replace:!0});break;case"b":Z.set(!Z.value);break;case"[":case"]":n.page==="group"&&Ea(n.path,e.key==="]"?1:-1);break}}async function Ea(e,t){let n=await Se(le()),a=Ds(ut(_(n),n?.meta?.sources??[]),e),o=a.findIndex(c=>c.path===e),i=a[o+t];i&&L(C(i.path))}function Ta(){let e=O(null);return T(()=>{let t=e.current;t.showModal();let n=()=>$e.set(!1);return t.addEventListener("close",n),()=>t.removeEventListener("close",n)},[]),s`<dialog class="sheet" ref=${e} aria-labelledby="help-title" closedby="any">
    <div class="help">
      <h3 class="heading" id="help-title">Keyboard shortcuts</h3>
      <table class="kv">${rt.map(([t,n])=>s`<tr><td><kbd class="small">${t}</kbd></td><td>${n}</td></tr>`)}</table>
      <form method="dialog" style="margin-block-start: 16px"><${ae} type="submit" icon="x" kind="quiet">Close<//></form>
    </div>
  </dialog>`}jt();if(ue){let e=new URLSearchParams(location.search).get("theme");(e==="light"||e==="dark")&&(me.value=e),document.documentElement.classList.add("rendering"),window.__btBusy=()=>Le.n,Gt&&Zt()}kn();var Ma=K("meta").then(e=>(ue&&(e={...e,settings:{...e.settings,theme_mode:me.value}}),it(e),e));!ue&&!!1&&Kt(async()=>{let[e,t]=await Promise.all([Ma,K("meta")]);e.bundle!==t.bundle?location.reload():it(t)});Rt(s`<${Rs} />`,document.getElementById("app"));
