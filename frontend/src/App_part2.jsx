                                        <input type="range" min="0.3" max="0.9" step="0.05" value={cfg.win_rate_target} onChange={e => updateConfig(cfg.asset_class, e.target.value)} className="flex-1 accent-blue-500" />
                                        <span className="text-lg font-bold text-white font-mono">{(cfg.win_rate_target * 100).toFixed(0)}%</span>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-10">
                    {[
                        { id: 'indices', name: 'Macro_Sync', desc: 'Global Indices & Market Mood vectors.' },
                        { id: 'stocks', name: 'Alpha_Universe', desc: 'Predictive Neural Models for Equity.' },
                        { id: 'fx', name: 'Liquidity_Layer', desc: 'FX Liquidity & Interest Differentials.' },
                        { id: 'commodities', name: 'Hard_Assets', desc: 'Energy & Metals sync.' },
                        { id: 'crypto', name: 'Digital_Compute', desc: 'On-chain velocity audits.' },
                        { id: 'hft', name: 'Velocity_HFT', desc: 'High-Frequency Pressure Values.' }
                    ].map(comp => (
                        <div key={comp.id} className="glass rounded-[3rem] p-10 border-white/10 shadow-2xl flex flex-col gap-10 group hover:border-blue-500/40 transition-all">
                            <div className="space-y-3"><h3 className="text-2xl font-black text-white uppercase italic tracking-tighter font-outfit group-hover:text-blue-400 transition-colors leading-none">{comp.name}</h3><p className="text-sm text-slate-500 leading-relaxed font-medium italic">"{comp.desc}"</p></div>
                            <div className="flex items-center justify-between mt-auto pt-10 border-t border-white/5"><div className="flex flex-col"><span className="text-[10px] font-black text-slate-600 uppercase font-outfit leading-none">Node_Status</span><span className={`text-base font-bold font-mono italic mt-1 ${maintenanceStatus[comp.id] === 'Live' ? 'text-emerald-400' : 'text-blue-400'}`}>{maintenanceStatus[comp.id] || 'IDLE'}</span></div><button onClick={() => triggerMaintenance(comp.id)} className="px-8 py-3.5 rounded-2xl text-[10px] font-black uppercase tracking-widest bg-white text-black hover:bg-blue-600 hover:text-white transition-all font-outfit shadow-xl active:scale-95">Sync_Node</button></div>
                        </div>
                    ))}
                </div>
            </div>
        )}

      </main>

      {/* --- HUD FOOTER --- */}
      <footer className="fixed bottom-0 left-0 w-full h-12 glass border-t border-white/5 backdrop-blur-3xl z-[110] flex items-center px-12 justify-between">
         <div className="flex items-center gap-8">
            <div className="flex items-center gap-2.5">
               <div className="h-2 w-2 bg-emerald-500 rounded-full animate-pulse shadow-[0_0_10px_#10b981]" />
               <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest font-outfit">Node_0.129.4 // OK</span>
            </div>
            <div className="h-4 w-px bg-white/5" />
            <div className="hidden md:flex items-center gap-2.5">
               <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest font-outfit">Neural Compute: 94.2 TFLOPS</span>
            </div>
         </div>
         <div className="hidden sm:flex items-center gap-6 text-[10px] font-black text-slate-600 uppercase tracking-widest font-outfit italic">Institutional v2.9 ELITE // Global Portfolio Control</div>
      </footer>
    </div>
  );
};

export default App;
