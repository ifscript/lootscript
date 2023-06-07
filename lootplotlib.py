#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@author: fscript
"""

import matplotlib.pyplot as plt
from scipy.optimize import curve_fit
import re
import numpy as np
import datetime as dt


def top10_pie(sorted_names,sorted_values,title,high_to_low=False):
    if high_to_low:
        idx1=0
        idx2=10
        step=1
    else:
        idx1=len(sorted_values)
        idx2=len(sorted_values)-11
        step=-1
    theta=sorted_values[idx1:idx2:step]
    beschriftung=sorted_names[idx1:idx2:step]
    farbe=[(0.7-(2*ii/np.sum(sorted_values)),0.7-(2*ii/np.sum(sorted_values)),0.8) for ii in theta]
    theta=np.append(theta,np.sum(sorted_values)-np.sum(sorted_values[idx1:idx2:step]))
    farbe.append((0.1,0.1,0.6))
    beschriftung=np.append(beschriftung,"Rest")
    fig=plt.figure(figsize=(9,9))
    ax=fig.add_subplot(1,1,1,aspect=1)
    ax.pie(theta, labels=beschriftung,radius=1,labeldistance=1.06,colors=farbe, autopct="%.1f%%",pctdistance=0.7)
    fig.suptitle(title, weight="bold")
    fig.savefig(f"{re.sub('[/ ]','_',title)}.png",dpi=300)
    fig.tight_layout()
    plt.close(fig)

def histograms(times,values=None,var_name="Beiträge",norm_values=None):
    jahresdaten=range(dt.datetime.fromtimestamp(times[0]).year,dt.datetime.fromtimestamp(times[-1]).year+1)
    jahrezahlen=[f"{int(ii)}" for ii in jahresdaten]
    month_bins=np.concatenate([[dt.datetime.timestamp(dt.datetime(ii,jj,1)) for jj in range(1,13)] for ii in jahresdaten])
    month_bins=np.append(month_bins,dt.datetime.timestamp(dt.datetime(jahresdaten[-1]+1,1,1))-1)
    jahresdaten=[dt.datetime.timestamp(dt.datetime(ii,1,1)) for ii in jahresdaten]
    if type(norm_values)==type(None):
        vals=values
    else:
        vals=np.concatenate([(np.divide(
            values[(times>=month_bins[jj]) & (times<month_bins[jj+1]+(1 if jj==len(month_bins)-1 else 0))],
            np.sum(norm_values[(times>=month_bins[jj]) & (times<month_bins[jj+1]+(1 if jj==len(month_bins)-1 else 0))])
            ) if np.sum(norm_values[(times>=month_bins[jj]) & (times<month_bins[jj+1]+(1 if jj==len(month_bins)-1 else 0))])>0
            else np.divide(np.ones(np.sum((times>=month_bins[jj]) & (times<month_bins[jj+1]+(1 if jj==len(month_bins)-1 else 0)))),
                           -np.sum((times>=month_bins[jj]) & (times<month_bins[jj+1]+(1 if jj==len(month_bins)-1 else 0)))))
            for jj in range(len(month_bins)-1)])
    fig = plt.figure(figsize=(9,9))
    gs = plt.GridSpec(2, 1)
    ax = fig.add_subplot(gs[0])
    jahreszeiten = ax.hist(times, bins=month_bins, rwidth=0.8, color=(.2,.2,.8), weights=vals)#, (0,7*24*60*60),log=True)
    ax.set_title(f"{var_name} pro Monat", fontdict={"fontweight":"bold"})
    ax.set_ylabel(var_name)
    ax.set_xticks(jahresdaten)
    ax.set_xticklabels(jahrezahlen)
    ax.vlines(jahresdaten,0,np.max(jahreszeiten[0])*1.05,linestyles='dashed',lw=0.8,color="k")
    ax.set_ylim(0,np.max(jahreszeiten[0])*1.05)
    Uhrzeiten=np.array([dt.datetime.fromtimestamp(ii).hour+(dt.datetime.fromtimestamp(ii).minute+dt.datetime.fromtimestamp(ii).second/60)/60 for ii in times])
    if type(norm_values)==type(None):
        vals=values
    else:
        month_bins=np.array([ii/2 for ii in range(49)])
        # print(np.concatenate([
        #     np.divide(values[np.logical_and(Uhrzeiten>=month_bins[jj],Uhrzeiten<month_bins[jj+1]+(1/(24*60*60) if jj==len(month_bins)-1 else 0))],
        #     np.sum(norm_values[np.logical_and(Uhrzeiten>=month_bins[jj],Uhrzeiten<month_bins[jj+1]+(1/(24*60*60) if jj==len(month_bins)-1 else 0))]))
        #     for jj in range(5,8)]))
        vals=np.concatenate([(np.divide(
            values[np.logical_and(Uhrzeiten>=month_bins[jj],Uhrzeiten<month_bins[jj+1]+(1/(24*60*60) if jj==len(month_bins)-1 else 0))],
            np.sum(norm_values[np.logical_and(Uhrzeiten>=month_bins[jj],Uhrzeiten<month_bins[jj+1]+(1/(24*60*60) if jj==len(month_bins)-1 else 0))])
            ) if np.sum(norm_values[(Uhrzeiten>=month_bins[jj]) & (Uhrzeiten<month_bins[jj+1]+(1 if jj==len(month_bins)-1 else 0))])>0
            else np.divide(np.ones(np.sum((Uhrzeiten>=month_bins[jj]) & (Uhrzeiten<month_bins[jj+1]+(1 if jj==len(month_bins)-1 else 0)))),
                           -np.sum((Uhrzeiten>=month_bins[jj]) & (Uhrzeiten<month_bins[jj+1]+(1 if jj==len(month_bins)-1 else 0)))))
            for jj in range(len(month_bins)-1)])
        Uhrzeiten.sort() # The weights are sorted.
    ax = fig.add_subplot(gs[1])
    tageszeiten = ax.hist(Uhrzeiten, 24*2, (0,24), rwidth=0.8, color=(.3,.3,.8), weights=vals)
    ax.set_xticks([0,2,4,6,8,10,12,14,16,18,20,22,24])
    ax.set_xticklabels(["00:00","02:00","04:00","06:00","08:00","10:00","12:00","14:00","16:00","18:00","20:00","22:00","24:00"])
    ax.set_title(f"{var_name} nach Tageszeit", fontdict={"fontweight":"bold"})
    ax.set_xlabel("Uhrzeit")
    ax.set_ylabel(var_name)
    plt.text(3,np.max(tageszeiten[0]),'Jeder Balken entspricht\neiner halbe Stunde.',size=8,
             horizontalalignment='center',verticalalignment='top',bbox=dict(facecolor='w',alpha=.8,edgecolor='#d0d0d0',boxstyle='round'))
    ax.set_ylim(0,np.max(tageszeiten[0])*1.05)
    ax.vlines([0,6,12,18,24],0,np.max(tageszeiten[0])*1.05,linestyles='dashed',lw=0.8,color="k")
    fig.tight_layout()
    fig.savefig(f"histogramm-{re.sub(r'[/ ]','_',var_name)}.png",dpi=300)
    plt.close(fig)
    
def top10_histogram(top10_names,post_names,post_times,values=None,var_name="Beiträge"):
    jahresdaten=range(dt.datetime.fromtimestamp(post_times[0]).year,dt.datetime.fromtimestamp(post_times[-1]).year+1)
    jahrezahlen=[f"{int(ii)}" for ii in jahresdaten]
    quart_bins=np.concatenate([[dt.datetime.timestamp(dt.datetime(ii,jj,1)) for jj in range(1,13,3)] for ii in jahresdaten])
    quart_bins=np.append(quart_bins,dt.datetime.timestamp(dt.datetime(jahresdaten[-1]+1,1,1))-1)
    jahresdaten=[dt.datetime.timestamp(dt.datetime(ii,1,1)) for ii in jahresdaten]
    histposter=[post_times[post_names==ii] for ii in top10_names]
    fig = plt.figure(figsize=(9,9))
    gs = plt.GridSpec(3, 1)
    ax = fig.add_subplot(gs[0])
    ax.set_title(f"Top 10 Spieler pro Quartal: {var_name}", fontdict={"fontweight":"bold"})
    jahreszeiten = ax.hist(post_times, bins=quart_bins, color="k",histtype="step", weights=values)
    ax.set_xlim(quart_bins[0],quart_bins[-1]+.2*(quart_bins[-1]-[quart_bins[0]]))
    ax.set_ylabel(f"Alle {var_name}")
    tk=ax.get_yticks()
    ax.vlines(jahresdaten,0,tk[-1],linestyles='dashed',lw=0.8,color="k")
    ax.set_ylim(tk[0],tk[-1])
    ax.set_yticks(tk[1:])
    ax.set_xticklabels([])
    if type(values)!=type(None):
        top10_value=[np.concatenate([np.divide(
            values[post_names==ii][np.logical_and(quart_bins[jj]<=post_times[post_names==ii],quart_bins[jj+1]>post_times[post_names==ii])],
            jahreszeiten[0][jj]) for jj in range(len(quart_bins)-1)]) for ii in top10_names]
    else:
        top10_value=[np.concatenate([np.divide(
            np.ones(np.sum([np.logical_and(quart_bins[jj]<=post_times[post_names==ii],quart_bins[jj+1]>post_times[post_names==ii])])),
            jahreszeiten[0][jj]) for jj in range(len(quart_bins)-1)]) for ii in top10_names]
    ax = fig.add_subplot(gs[1:])
    farben=[(0.5+(i*((-1)**i))/25.0,1-float(i)/10.0,((i-5)/5.0)**2) for i in range(10)]
    ax.hist(histposter,  bins=quart_bins, rwidth=0.8, histtype='barstacked', label=top10_names, weights=top10_value, color=farben)
    ax.set_xlim(quart_bins[0],quart_bins[-1]+.2*(quart_bins[-1]-[quart_bins[0]]))
    ax.set_ylabel(f"Anteil der {var_name}")
    ax.set_yticks([0,.2,.4,.6,.8,1])
    ax.set_yticklabels(["0%","20%","40%","60%","80%","100%"])
    ax.set_xticks(jahresdaten)
    ax.set_xticklabels(jahrezahlen)
    ax.vlines(jahresdaten,0,1,linestyles='dashed',lw=0.8,color="k")
    ax.set_ylim(0,1)
    ax.legend(loc='upper right',ncol=1)
    ax.text(quart_bins[0]+.02*(quart_bins[-1]-[quart_bins[0]]),.98,'Der leere Bereich\nentspricht dem Rest.',
            ha="left",va="top",size=10,bbox=dict(facecolor='w',edgecolor='#d0d0d0',boxstyle='round'))
    fig.tight_layout()
    fig.subplots_adjust(hspace=0)
    fig.savefig(f"top10-{re.sub(r'[/ ]','_',var_name)}-histogramm.png",dpi=300)
    plt.close(fig)
    
def time_decay_plots(post_times,life_times):
    jahresdaten=range(dt.datetime.fromtimestamp(post_times[0]).year,dt.datetime.fromtimestamp(post_times[-1]).year+2)
    jahrezahlen=[f"{int(ii)}" for ii in jahresdaten[:-1]]
    jahresdaten=[dt.datetime.timestamp(dt.datetime(ii,1,1)) for ii in jahresdaten]
    njahre=len(jahrezahlen)
    if njahre<3:
        fig = plt.figure(figsize=(9,9/njahre))
        gs = plt.GridSpec(njahre,1)
    else:
        fig = plt.figure(figsize=(9,3*int(.9+njahre/3)))
        gs = plt.GridSpec(int(.9+njahre/3),3)
    for ii in range(njahre):
        ax = fig.add_subplot(gs[ii])
        c,b,r=ax.hist(
            life_times[np.logical_and(jahresdaten[ii]<=post_times,jahresdaten[ii+1]>post_times)],
            24*7, (0,7*24*60*60),log=True, color=(.2,.2,.8))
        ax.set_xticks(range(0,8*60*60*24,60*60*24))
        ax.set_xticklabels(("0","1","2","3","4","5","6","7"))
        ax.set_yticks((1,10,100,1000))
        ax.set_yticklabels(("1","10","100","1000"))
        ax.set_title(f"Zeit nach Beitrag in {jahrezahlen[ii]}", fontdict={"fontweight":"bold"})
        ax.set_xlabel("Tage")
        ax.set_ylabel("Beiträge")
        def linf(x,t,bb): return np.multiply(bb,np.exp(np.divide(-x,t)))
        val,cov=curve_fit(linf,np.subtract(b[1:],30*60),c,p0=(60*60*4,1e3))
        ax.plot(b,linf(b,*val),":", color=(.6,.6,.8),lw=.8)
        ax.set_ylim(0.8,1e3)
        t=int(np.log(2)*val[0])
        ax.text(1.5*24*60**2,600,"$t_{1/2}$ ="+" {} Min. {} Sek.".format(int(t/60),int(t-60*int(t/60))),
                size=8,bbox=dict(facecolor='w',edgecolor='#d0d0d0',boxstyle='round'))
    fig.tight_layout()
    plt.savefig("lifetime_decayplots.png",dpi=300)
    plt.close(fig)

def top10_by_year(post_names,post_times,values=None,var_name="Beiträge",norm_values=None,min_posts_filter=3):
    jahresdaten=range(dt.datetime.fromtimestamp(post_times[0]).year,dt.datetime.fromtimestamp(post_times[-1]).year+2)
    jahrezahlen=[f"{int(ii)}" for ii in jahresdaten[:-1]]
    jahresdaten=[dt.datetime.timestamp(dt.datetime(ii,1,1)) for ii in jahresdaten]
    njahre=len(jahrezahlen)
    if njahre==1:
        fig = plt.figure(figsize=(9,9))
        gs = plt.GridSpec(1,1)
    else:
        fig = plt.figure(figsize=(9,int(.9+njahre/2)*4))
        gs = plt.GridSpec(int(.9+njahre/2),2)
    fig.suptitle(f"Jährliche Top 10\n Gemessen an: {var_name}",weight="bold",size=24)
    for jj in range(njahre):
        ax = fig.add_subplot(gs[jj])
        names=post_names[(post_times>=jahresdaten[jj]) & (post_times<jahresdaten[jj+1])]
        if type(values)==type(None):
            vals=np.ones(len(names))
        else:
            vals=values[(post_times>=jahresdaten[jj]) & (post_times<jahresdaten[jj+1])]
        if type(norm_values)==type(None):
            player_sub=np.array([(ii,np.sum(vals[names==ii])/np.sum(vals)) for ii in np.unique(names)]
                              ,dtype=[('Spieler',"U32"),('Anteil',"float32")])
            player_sub.sort(order='Anteil')
            theta=np.append([1-np.sum(player_sub["Anteil"][-10:])],player_sub["Anteil"][-10:])
            ax.set_xticks(np.divide(range(0,int(5*(2+np.max(theta)//.05)),5),100))
            ax.set_xticklabels([f"{ii}%" for ii in range(0,int(5*(2+np.max(theta)//.05)),5)], rotation=45)
            ax.set_xlim(0,int(5*(1+np.max(theta)//.05))/100)
        else:
            nvals=norm_values[(post_times>=jahresdaten[jj]) & (post_times<jahresdaten[jj+1])]
            nn,cc=np.unique(names,return_counts=True)
            player_sub=np.array([(ii,np.sum(vals[names==ii])/(np.sum(nvals[names==ii]) if np.sum(nvals[names==ii])>0 else 1))
                                 for ii in nn[cc>min_posts_filter]]
                          ,dtype=[('Spieler',"U32"),('Anteil',"float32")])
            player_sub.sort(order='Anteil')
            theta=np.append([
                np.sum(vals[np.logical_not(np.isin(names,player_sub["Spieler"][:-10]))])/
                np.sum(nvals[np.logical_not(np.isin(names,player_sub["Spieler"][:-10]))])],
                player_sub["Anteil"][-10:])
        ax.barh(range(11),theta, color=(.2,.2,.8))
        ax.set_ylim(-0.8,12.5)
        ax.set_yticks(range(11))
        ax.set_yticklabels(np.append(["Rest"],player_sub["Spieler"][-10:]), rotation=0)
        ax.set_title(f"Top 10 Spieler {jahrezahlen[jj]}", size=12, fontdict={"fontweight":"bold"})
        ax.text(ax.get_xlim()[-1]/2,11.5,
                f"insgesamt {len(player_sub['Spieler'])} Spieler\n und {int(np.sum(vals))} {var_name}",
                horizontalalignment="center",va="center",size=10)
    fig.tight_layout() 
    fig.savefig(f"top10byYear-{re.sub(r'[/ ]','_',var_name)}.png",dpi=300)
    plt.close(fig)