/* BOAT EDGE V256: mobile-first home navigation.
 * Move existing venue sections (and their event handlers) ahead of marketing
 * and watchlists. No data, race, prediction, odds, result, or formal modification.
 */
(function(){
'use strict';
if(typeof window==='undefined'||typeof document==='undefined')return;
if(window.BoatEdgeV256)return;
function layout(){
 const home=document.getElementById('homeView');
 if(!home)return false;
 const toolbar=home.querySelector('.venue-toolbar');
 const venueList=home.querySelector('#venues');
 const spotlight=home.querySelector('.home-command');
 if(!toolbar||!venueList||!spotlight)return false;
 const searchSection=toolbar.closest('section');
 const venueSection=venueList.closest('section');
 if(!searchSection||!venueSection||searchSection===venueSection||
    searchSection.parentElement!==home||venueSection.parentElement!==home||
    spotlight.parentElement!==home)return false;
 // DOM move keeps the original search/filter and race-button listeners alive.
 // No clone, innerHTML rewrite or source mutation.
 if(searchSection.nextElementSibling!==venueSection||
    venueSection.nextElementSibling!==spotlight){
  home.insertBefore(searchSection,spotlight);
  home.insertBefore(venueSection,spotlight);
 }
 document.documentElement.classList.add('be256-venue-first');
 return true;
}
if(typeof module!=='undefined'&&module.exports)module.exports={layout};
function start(){
 layout();
 // Existing app redraws individual venue cards only; observe no race events.
 document.addEventListener('visibilitychange',function(){if(!document.hidden)layout()});
 // iPhone Safari can restore a page from back-forward cache without DOMContentLoaded.
 // Reapply the idempotent DOM move; never recreate venue/race controls.
 window.addEventListener('pageshow',function(event){if(event.persisted)layout()});
}
window.BoatEdgeV256={layout:layout,version:'V256-MOBILE-VENUE-FIRST'};
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',start,{once:true});else start();
})();