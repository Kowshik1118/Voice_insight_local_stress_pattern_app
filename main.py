"""Voice Insight — local, non-clinical vocal-pattern analyser.
Uses only Python's standard library. It never uploads or stores audio.
"""
import wave, struct, math, statistics, threading
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

BG='#0B1020'; PANEL='#151D35'; PANEL2='#1B2746'; TEXT='#F4F7FF'; MUTED='#A9B7D0'; ACCENT='#6C8CFF'; TEAL='#38D9C0'; AMBER='#FFBE55'; RED='#FF6B7A'

class AudioAnalyzer:
    """Fast chunk-based analysis for uncompressed PCM WAV files."""
    def analyze(self, path):
        with wave.open(path, 'rb') as wf:
            channels, width, rate, frames = wf.getnchannels(), wf.getsampwidth(), wf.getframerate(), wf.getnframes()
            if width not in (1, 2, 3, 4): raise ValueError('Supported WAV sample widths: 8, 16, 24, or 32-bit PCM.')
            if wf.getcomptype() != 'NONE': raise ValueError('Please select an uncompressed PCM WAV file.')
            duration = frames / rate
            if duration < 1: raise ValueError('Use audio at least one second long.')
            chunk_frames=max(1, int(rate*.20)); energies=[]; zcrs=[]; active=0; count=0
            while True:
                raw=wf.readframes(chunk_frames)
                if not raw: break
                samples=self._decode(raw,width,channels)
                if not samples: continue
                rms=math.sqrt(sum(x*x for x in samples)/len(samples))
                energies.append(20*math.log10(max(rms,1e-9)))
                crossings=sum(1 for a,b in zip(samples,samples[1:]) if (a>=0)!=(b>=0))
                zcrs.append(crossings/max(1,len(samples)-1))
                count+=1
            noise_floor=statistics.quantiles(energies,n=10)[1] if len(energies)>=10 else min(energies)
            threshold=noise_floor+8
            active_flags=[e>threshold for e in energies]; active=sum(active_flags)
            pauses=(len(energies)-active)/max(1,len(energies))*100
            active_e=[e for e,a in zip(energies,active_flags) if a] or energies
            active_z=[z for z,a in zip(zcrs,active_flags) if a] or zcrs
            mean_db=statistics.mean(active_e); variability=statistics.pstdev(active_e) if len(active_e)>1 else 0
            zvar=statistics.pstdev(active_z) if len(active_z)>1 else 0
            # Transparent heuristic: a vocal-pattern flag, not a stress diagnosis.
            energy_score=self._scale(mean_db,-38,-12)*30
            variation_score=self._scale(variability,2,10)*25
            pace_score=self._scale(statistics.mean(active_z),.03,.16)*20
            pause_score=self._scale(pauses,5,45)*25
            score=round(min(100,max(0,energy_score+variation_score+pace_score+pause_score)))
            level='Lower pattern change' if score<35 else 'Moderate pattern change' if score<65 else 'Higher pattern change'
            return {'duration':duration,'rate':rate,'channels':channels,'mean_db':mean_db,'variation':variability,'pause_pct':pauses,'zcr':statistics.mean(active_z),'score':score,'level':level,'chunks':count}
    def _scale(self,x,lo,hi): return min(1,max(0,(x-lo)/(hi-lo)))
    def _decode(self,raw,width,channels):
        vals=[]
        if width==1: vals=[(b-128)/128 for b in raw]
        elif width==2: vals=[x/32768 for x in struct.unpack('<%dh'%(len(raw)//2),raw)]
        elif width==3:
            for i in range(0,len(raw)-2,3):
                n=int.from_bytes(raw[i:i+3],'little',signed=True); vals.append(n/8388608)
        else: vals=[x/2147483648 for x in struct.unpack('<%di'%(len(raw)//4),raw)]
        return [sum(vals[i:i+channels])/channels for i in range(0,len(vals)-channels+1,channels)]

class App(tk.Tk):
    def __init__(self):
        super().__init__(); self.title('Voice Insight — Local Audio Patterns'); self.geometry('1020x700'); self.minsize(900,620); self.configure(bg=BG)
        self.path=None; self.result=None; self._style(); self._build()
    def _style(self):
        s=ttk.Style(self); s.theme_use('clam'); s.configure('TProgressbar',troughcolor=PANEL2,background=ACCENT,lightcolor=ACCENT,darkcolor=ACCENT,bordercolor=PANEL2)
    def card(self,parent): return tk.Frame(parent,bg=PANEL,highlightthickness=1,highlightbackground='#253356')
    def label(self,parent,text,size=12,color=TEXT,bold=False,**kw): return tk.Label(parent,text=text,bg=parent['bg'],fg=color,font=('Segoe UI',size,'bold' if bold else 'normal'),**kw)
    def _build(self):
        header=tk.Frame(self,bg=BG); header.pack(fill='x',padx=38,pady=(28,12))
        self.label(header,'VOICE INSIGHT',12,TEAL,True).pack(anchor='w')
        self.label(header,'Local vocal-pattern analysis',27,TEXT,True).pack(anchor='w',pady=(3,2))
        self.label(header,'A privacy-first reflection tool — not a medical or psychological diagnosis.',11,MUTED).pack(anchor='w')
        choose=self.card(self); choose.pack(fill='x',padx=38,pady=14)
        self.file_text=tk.StringVar(value='Choose an uncompressed PCM WAV recording to begin')
        self.label(choose,'Audio file',11,MUTED,True).pack(anchor='w',padx=20,pady=(16,3))
        row=tk.Frame(choose,bg=PANEL); row.pack(fill='x',padx=20,pady=(0,16))
        self.label(row,'',12,TEXT,anchor='w',textvariable=self.file_text).pack(side='left',fill='x',expand=True)
        tk.Button(row,text='Select WAV',command=self.pick,bg=ACCENT,fg='white',activebackground='#87A0FF',activeforeground='white',relief='flat',font=('Segoe UI',10,'bold'),padx=18,pady=9,cursor='hand2').pack(side='right')
        self.status=tk.StringVar(value='Everything runs on this device. No API, server, database, or account is used.')
        self.label(self,self.status.get(),10,MUTED).pack(anchor='w',padx=42,pady=(0,8))
        self.status_label=self.label(self,'',10,MUTED); self.status_label.pack(anchor='w',padx=42)
        body=tk.Frame(self,bg=BG); body.pack(fill='both',expand=True,padx=38,pady=(8,28)); body.columnconfigure((0,1,2),weight=1); body.rowconfigure(0,weight=1)
        self.score_card=self.card(body); self.score_card.grid(row=0,column=0,sticky='nsew',padx=(0,10))
        self.metrics_card=self.card(body); self.metrics_card.grid(row=0,column=1,sticky='nsew',padx=5)
        self.note_card=self.card(body); self.note_card.grid(row=0,column=2,sticky='nsew',padx=(10,0))
        self.render_empty()
    def clear(self,frame):
        for w in frame.winfo_children(): w.destroy()
    def render_empty(self):
        for c in (self.score_card,self.metrics_card,self.note_card): self.clear(c)
        self.label(self.score_card,'PATTERN SCORE',11,MUTED,True).pack(anchor='w',padx=20,pady=(20,8)); self.label(self.score_card,'—',58,TEXT,True).pack(pady=(20,5)); self.label(self.score_card,'Select a WAV file',11,MUTED).pack()
        self.label(self.metrics_card,'VOICE METRICS',11,MUTED,True).pack(anchor='w',padx=20,pady=20)
        for x in ('Average vocal energy','Energy variation','Estimated quiet time','Speech activity proxy'): self.label(self.metrics_card,x+'  —',11,TEXT).pack(anchor='w',padx=20,pady=9)
        self.label(self.note_card,'HOW TO READ THIS',11,MUTED,True).pack(anchor='w',padx=20,pady=20)
        note='The score reflects changes in energy, variation, silence and speaking activity. Room noise, microphone distance, illness, emotion and recording quality can affect it.'
        self.label(self.note_card,note,11,TEXT,wraplength=230,justify='left').pack(anchor='w',padx=20)
    def pick(self):
        p=filedialog.askopenfilename(title='Choose WAV audio',filetypes=[('WAV audio','*.wav'),('All files','*.*')])
        if not p:return
        self.path=p; self.file_text.set(p.split('/')[-1]); self.status_label.config(text='Analysing locally…')
        threading.Thread(target=self.run,daemon=True).start()
    def run(self):
        try: r=AudioAnalyzer().analyze(self.path); self.after(0,lambda:self.render(r))
        except Exception as e: self.after(0,lambda:messagebox.showerror('Cannot analyse audio',str(e)))
    def render(self,r):
        self.result=r; self.status_label.config(text=f"Analysis complete • {r['duration']:.1f} seconds • {r['rate']} Hz • {r['channels']} channel(s)")
        for c in (self.score_card,self.metrics_card,self.note_card): self.clear(c)
        color=TEAL if r['score']<35 else AMBER if r['score']<65 else RED
        self.label(self.score_card,'PATTERN SCORE',11,MUTED,True).pack(anchor='w',padx=20,pady=(20,2)); self.label(self.score_card,str(r['score']),58,color,True).pack(pady=(8,0)); self.label(self.score_card,'out of 100',10,MUTED).pack(); self.label(self.score_card,r['level'],12,color,True).pack(pady=(16,4)); ttk.Progressbar(self.score_card,maximum=100,value=r['score']).pack(fill='x',padx=20,pady=8)
        self.label(self.metrics_card,'VOICE METRICS',11,MUTED,True).pack(anchor='w',padx=20,pady=20)
        vals=[('Average vocal energy',f"{r['mean_db']:.1f} dBFS"),('Energy variation',f"{r['variation']:.1f} dB"),('Estimated quiet time',f"{r['pause_pct']:.0f}%"),('Activity proxy',f"{r['zcr']:.3f}")]
        for a,b in vals:
            row=tk.Frame(self.metrics_card,bg=PANEL); row.pack(fill='x',padx=20,pady=9); self.label(row,a,11,TEXT).pack(side='left'); self.label(row,b,11,TEAL,True).pack(side='right')
        self.label(self.note_card,'RESPONSIBLE USE',11,MUTED,True).pack(anchor='w',padx=20,pady=20)
        note='This application does not detect or diagnose stress, anxiety, deception, mental health conditions, or emotion. It only summarizes acoustic patterns in one recording. Compare recordings made with similar microphones and environments.'
        self.label(self.note_card,note,11,TEXT,wraplength=235,justify='left').pack(anchor='w',padx=20)
        self.label(self.note_card,'Privacy',11,MUTED,True).pack(anchor='w',padx=20,pady=(25,5)); self.label(self.note_card,'Audio remains on your computer and is not saved by this app.',11,TEAL,wraplength=235,justify='left').pack(anchor='w',padx=20)
if __name__=='__main__': App().mainloop()
