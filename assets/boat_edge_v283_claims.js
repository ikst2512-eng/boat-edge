/* BOAT EDGE V283: UI-only operational proof labels.
 * No network calls, no results, no predictions and no model changes. */
(()=>{'use strict';
 const JST={timeZone:'Asia/Tokyo'};
 const today=now=>new Date(now).toLocaleDateString('sv-SE',JST);
 function formalGuard(formal,now=Date.now()){
   const g=formal?.guards||{};
   const t=typeof formal?.asOf==='string'?Date.parse(formal.asOf):NaN;
   const age=now-t;
   const fresh=Number.isFinite(t)&&age>=-300000&&age<=2700000&&
     new Date(t).toLocaleDateString('sv-SE',JST)===today(now);
   const closed=Boolean(fresh&&g.results_seen===false&&g.unlock===false&&g.scoring===false&&
     g.RESULT_UNLOCK_TOKEN===null&&formal?.formalFirst100?.races===0&&
     formal?.connected===false&&formal?.predictions_ready===false);
   return {closed,fresh};
 }
 function claim(formal,now=Date.now()){
   const p=formalGuard(formal,now);
   return {
     closed:p.closed,
     text:'GitHub Actions PASS＝自動テストの成功、Pages SUCCESS＝公開処理の成功。いずれも予想精度向上やSafari実画面の確認を証明しません。'+
       (p.closed?'正式Fresh：当日データで結果未見ロック確認済み（0/100R）。未証明候補は本番未採用。':
         '正式Fresh：新鮮なロック証拠を確認できないため未確認。解除や採点は不可。')
   };
 }
 window.BoatEdgeV283Claims={formalGuard,claim};
})();