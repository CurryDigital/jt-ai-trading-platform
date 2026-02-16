        {activeTab === 'hft' && (
            <div className="space-y-16 animate-in fade-in slide-in-from-bottom-6 duration-700 text-left">
                <div className="flex flex-col md:flex-row md:items-baseline justify-between gap-8 border-b border-white/5 pb-8">
                   <div className="flex items-baseline gap-6">
                      <h2 className="text-2xl md:text-3xl font-black text-white italic font-outfit leading-none uppercase tracking-tightest font-outfit">HFT Operations</h2>
                      <button onClick={() => setIsModalOpen(true)} className="h-10 w-10 rounded-full glass border-white/20 flex items-center justify-center text-lg font-black text-slate-400 hover:text-blue-400 transition-all">?</button>
                   </div>
                   <div className="flex items-center gap-4">
                      <div className="flex flex-col text-right">
                         <span className="text-[9px] font-black text-slate-500 uppercase tracking-widest font-outfit">IBKR_Bridge</span>
                         <span className={`text-xs font-bold font-mono ${ibStatus.web === 'Authenticated' ? 'text-emerald-400' : 'text-rose-400'}`}>{ibStatus.web}</span>
                      </div>
                      {ibStatus.web !== 'Authenticated' ? (
                          <a href="/sso/Login?forwardTo=22" target="_blank" rel="noopener noreferrer" 
                            className="px-6 py-2 rounded-xl bg-blue-600 text-white text-[10px] font-black uppercase border border-blue-500 shadow-lg glow-blue font-outfit leading-none">
                            Login_to_IBKR
                          </a>
                      ) : (
                          <button onClick={connectIb} className="px-6 py-2 rounded-xl bg-white/5 hover:bg-blue-600 text-slate-300 hover:text-white text-[10px] font-black uppercase border border-white/10 transition-all font-outfit shadow-lg leading-none">Init_Socket</button>
                      )}
                   </div>
                </div>

                {/* LIQUIDITY VECTORS */}
                <div className="space-y-6">
                   <h3 className="text-xl font-black text-white uppercase tracking-widest font-outfit opacity-60 italic">Real-Time Liquidity Matrix</h3>
                   <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
                       {hft.map((h, i) => (
                           <div key={i} className="glass rounded-[2.5rem] p-10 border-white/10 shadow-2xl flex flex-col gap-10 group hover:border-blue-500/30 transition-all relative overflow-hidden">
                               <div className="absolute top-0 right-0 p-8 opacity-[0.03] text-7xl font-black italic select-none font-outfit">{h.asset_class}</div>
                               <div className="space-y-2"><span className="text-4xl md:text-5xl font-black text-white italic tracking-tighter group-hover:text-blue-400 transition-colors uppercase leading-none font-outfit">{h.ticker}</span><div className="text-[10px] text-slate-500 uppercase font-black tracking-widest mt-2 flex items-center gap-2 font-outfit"><div className="h-1.5 w-1.5 bg-blue-500 rounded-full animate-pulse shadow-[0_0_8px_#3b82f6]" /> Liquidity: {h.liquidity_momentum}</div></div>
                               <div className="space-y-5"><div className="flex justify-between items-center bg-black/40 p-5 rounded-2xl border border-white/5"><div className="flex flex-col text-left font-outfit"><span className="text-[8px] text-slate-500 uppercase font-black tracking-widest font-outfit">Fusion Signal</span><span className={`text-xl font-black italic ${h.fusion_signal?.includes('BUY') ? 'text-emerald-400' : 'text-orange-400'}`}>{h.fusion_signal || 'NEUTRAL'}</span></div><div className="flex flex-col text-right font-outfit"><span className="text-[8px] text-slate-500 uppercase font-black tracking-widest font-outfit">Pressure Val</span><span className="text-xl font-bold text-white font-mono">{(h.pressure_value || 0).toFixed(2)}</span></div></div><p className="text-sm text-slate-400 italic leading-relaxed font-medium font-outfit">"{h.reasoning}"</p></div>
                           </div>
                       ))}
                   </div>
                </div>

                {/* QUANT STRATEGY LAYER */}
                <div className="space-y-10 pt-10 border-t border-white/5">
                   <h3 className="text-xl font-black text-white uppercase tracking-widest font-outfit opacity-60 italic">Leveraged Execution Matrix</h3>
                   <div className="glass rounded-[3rem] overflow-hidden shadow-2xl border-white/10 divide-y divide-white/5">
                        {[...fx, ...crypto.filter(c => ['BTC-USD', 'ETH-USD', 'SOL-USD'].includes(c.ticker))].map((item, idx) => (
                            <div key={idx} className="flex flex-col">
                                <HighDensityCard item={item} type={item.pair ? "FX" : "CRYPTO"} />
                                {item.drivers && (
                                    <div className="bg-blue-600/[0.03] border-t border-white/5 p-8 grid grid-cols-1 md:grid-cols-3 gap-6">
                                        {Object.entries(item.drivers).map(([key, strat]) => (
                                            <div key={key} className="glass p-6 rounded-[2rem] border-white/5 hover:border-blue-500/20 transition-all group">
                                                <div className="flex justify-between items-start mb-4"><div><h5 className="text-lg font-black text-white italic font-outfit uppercase">{strat.name}</h5><span className="text-[10px] font-black text-blue-500 uppercase tracking-widest">{strat.margin} Margin</span></div><div className="text-right font-outfit"><span className="text-[8px] font-black text-slate-500 uppercase block mb-1">Backtest WR</span><span className="text-xl font-bold text-white font-mono">{(strat.results.win_rate * 100).toFixed(0)}%</span></div></div>
                                                <p className="text-xs text-slate-400 italic mb-4 font-outfit">"{strat.logic}"</p>
                                                <div className="flex justify-between items-center pt-4 border-t border-white/5 font-outfit"><span className="text-[9px] font-black text-slate-600 uppercase">Est. Annual Alpha</span><span className={`text-base font-black font-mono ${strat.results.alpha.includes('+') ? 'text-green-400' : 'text-red-400'}`}>
                                                    {strat.results.alpha}
                                                </span></div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        ))}
                   </div>
                </div>
            </div>
        )}
