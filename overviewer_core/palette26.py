"""Minecraft 26.3 compact/lowercase block states; legacy palettes pass through.

Defaults: mcmeta 26.3-summary d96c75fec200c4580dd75e033a76341521165461,
generated from Minecraft 26.3 block report. Embedded to avoid runtime downloads.
"""
import base64
import json
import zlib

_DATA = (
    'c-pO8;g0Mmu6~#PJwMLu-PK;rtBghwl~7fgPC}L>U0r8&-~AeFgAJs*XSLFiPW!WQ2mxbbQ@{WI?>BR^Z@<0$c>BL!et)}IyL;#M'
    '?d_Mh-t_x{e|S&O-T7ndu9JIM5A@Z$ZMQ==_7<pjJFW2FY$vyLfX_fIcE4NSJ&fOhTHS7TXM?KsnAi6)$!*8Y_^vlgP_#Xu8{Nfv'
    '|LiWub_Zy8zQ5yhyWYF-oc%Fw`?%b?k8z1Aq1CGByEXgUAAkHJUh<c>pmqfQZ*NyKZ8pAkZ$2zFE5)tZ_9P4M<NSUX^yUslAFCi9'
    'R<sSzxsKjePq>;MdJP2Xj{R}HGeP^^PS<XRA%KrES1s>my279MHA1^}-1|F^P%XXO@Ik5bd*(jOZvEtLH#?{<&(O*{7@ie$n%gne'
    'FECjczAe7MqSeMJW#)@>+-Tno^l%WJ7{<-`SwUZn`5N9=H7LJAHSoJ1*M}JVx*Nq;sGlO$ba&_8&vp4Q%}2KY^uI5L*1!rIO-J9Q'
    '+s4}x=4TwQ3LRnomtgqTutZAKkMjmAuz&~S-#cgCOZ?AcxlOi2(`PU6hJw{V^A_&b3D$IhZmU1~N-fxj73_#Y<?zmSi63-w&VTn~'
    'UF<ZmlFu>B&(DaHNm`+)DFmMKyTBI%%|tw$8}i4wOs;>A<YuNleI9Iqe{%y^5=orC7m5)<a_OTz*SoO-Ap4lU9yU%SH6OtAZ4=D1'
    'xXz#HiQ{s$(LzfB`r@dG2-1^2J2Df=>|+?7T|#-M$o&#sa{V0^3hWTKX}sNcIZ;qHk<?(d#!q(Z;Zy5oZW_T54qX~;npva<3087='
    '_}8uD1R&7=I$-DdnQ5AS*pvurx`ovpW}*82C0Ys>Ga}<+MigMFLQRVjt%S>oQgL`kWxSX=HC{eK&5sf-g^L+e<7I<JPg<QQCQFT1'
    '4dkRK(Nb7Xg90su**H}rP7E6G59<e0%-yo7Y*ARAu;i_I59Sa27Qcf~SgyZ;OA*$Y4P9Eyet0li%6Cz%YOQCxPw(Izz*V@LF<4;x'
    'xw<XPA`OooW)u_da~#H>wa~+So`EN7k@;HR1H89;u<8}N&A>N*?cQ}T8x|g<%eY6uA0+h7?g1=j@V2Cetv{xBa8F^!cy6h^+jk)s'
    'U76i1efVhqd@=G{Z?0E24Pgr_H0}Nn4iNcM?EkQPMa~Y9<m*H#`ha19%x>GDyD-_fv*22H+cD44D@lIS9meWiJB8=H4nu$~z}-w*'
    'hba!?ufY)<_ire=Or{TG8Cr%NayqP_yn8H}%zr$MfNvi5I6+w}m~riOS}kI_*)+~VVg{de*-ZwV2MZ<yAhZy@4*Sd`xN$Zz@wmgx'
    '%H$Iq5%*x42JUYBP0T)Tx7EO#!}Ng|i-p`WjKPr<OTHa1garVrVFs%^WOt*Wy@f3{MogN+4~uK*<|aFLVbQ`9!gP+)wBd4nVOLO3'
    'uwgi(wH+w9r6DNT%DyytuhqA$O;f0{Ev3{;K8>V@3H~~`I2*jd_Au}ExN+@S-F4S%)WITLQj8Imc1Mhf{RlcsPdI8wYj&`cdD4ol'
    'Iu<5`>Uztw#)*^_YO@EUvH?OK`xnN5eJu<j!QK7|=1b7zMls2*64TkYVFb?z!Xz(Mv0KA*_FNcIifH|_TfuPlOBnIO`CyFw3#Q2g'
    'XfYZ+FnHgOeP5q9GzPg54BtXmrV+++iQV6V?U;@^Odz!KA2#i$|IO}|9iihSxhK=(^gc)wKa5Cz7LoB$^fx^zQgO?Py9%G9B!id$'
    '^5DXkEQF|6-rSVF<8les-@&M*fjUB<l??iJZ0p#M4&D#8oew+3L#~8vU|6Z)e|1QMm-C<L{pRGM1$(tiJoBUQCy{ZvCMxdqU>u-R'
    'LwB1DI3+6{@x|@A&57Tt$)eTI>d69MjNe4SoVdYbXsSs@gGGzogA}SZ(RFBQL+_)>iq11>BkRMD6i!OBsc=|M`146ic4SVNWb?Qm'
    'bQp5+W1q)Ejt!Z?rnYiNrB_WRl66Gasi}bsViH8JswwJY+|*!@tz{h)VrBBP>R{7nP`r~jJMj^idxl4Mu-SLo7aBaZhTDNa+?weO'
    '_KTnZI<@WLC`ufH{*@p@8P`{aB0Ul88*D7_-VZZPYzwFlgv2>V1h^rKf${3vDAO+3U2&SF8A^SYQ7SXMk5d*N!KKRT>=Nc$Ji3!@'
    'VL2{BDg;>&Pt=b_Mnl1T3>r|&kFb2+m51z0fs$2@Tw+v1mpI!oU5~oKeq65!^y4-g@UBwpFxy)%5mzhB0o6NnHI!T>(|BL%SPLU6'
    '_EGV3uW7R1ZXBiF&EDVBKD{4)hj{>emV|Me;?$=3o_yr!n}jy^xV%~Z6I|WlmAj9bnebxq{h*i6j%ZTxw69x-`H1J$-PN0!S1?G1'
    'hV;sfb~pG`IK1C!(RTJ}!@nFmz5pM1COU5UiKIO`)3hxoAnm>hp{+5|ll_R<#k5%^j%t>+nT)hnPG-ifCegHQWLk^UHbQh7y>f)j'
    '@-c>?<SbC9vY!bpvYqG{fwd1?3|LbL7#)ZvPWV2sdn`*Fhv+4=g%4ZGM(?R9964ILH~u5{E`B{a?55YEjV!i`DOh%_T2F`!{eZy)'
    'cO>hJ4o$0VWazf&Sha-%M@#=1#?5shl(2r$9#%_-U~5If^Ez+W=x+4L+AZel8R2{}yK1dg%+n3Y8*4QnmX?p6S4%oF3R!f%n$pP9'
    '@*W+QO4!GfaVZJT#H8m?Tx>n8t;km_^p;wRk)u_U1Jx2ImXvQUV?HzJ%<PVMXz?qVY#5@|g3*mm+&B#=x1Fh>bUYpA!WUWX@-l7x'
    '#i7XV%{pMhlZ>uJqS+My8D5Ft;*|&)V*w>|EU>~e7MvK-2%1c{K$6iGSfRdjt_3UEbcvzi76_ScfsnOU$Y=8jP2a!bzv$vg3?L;='
    'dEcBk+uf{q{OV0gB)yy}A%KXnMsm9oLQ@BPQZx1yoas29GKq)uZt1;M+HikzZYnU`J_Qzz-y6*jTegmFn;>HXpl*rVmugB=KGQmg'
    'sPT+cfkeS7UMJ^P88~+Sx*3Z(imK<hEvk;EMW+$rUS~!T#xxi)kjXfOG6^Vynatot(0CUPbtLd?yc}+X>g6aM(-4ijwvr|Lk!YE_'
    'sT9a9TWOKmos(9Leq#QoAwQS;Q*NjdPP=p=Pc|?kRj637nja{KiwRP(RzlTO;>1<eS@sZAU$doa%z|W&GZM34m1=Y+l;Y%!*Cy#a'
    '!hI=HGwX%jh;tjfa)~5PHSNpjxMsviQ^0Yv%5+}R<r_8@J7*Q^@g)aLk1*D{B${en5{)}hsj7<D6(`5z3f2#naeM+BEw|aZ{oa-R'
    'BKYKS#BFhK+s|}s;*@RV*+GdWTAUwfEK#X&BhjBHYo>58P9<J0yvoUF$-L%b4!ZjM<V36Q$qDL8m|bWg{n~}$!r(h_g9kI&>;APT'
    'EF2l_?<!wc`?=c3E&SWkw{82i(x=t_Z0XAiKla3jE&W&RyK28x`>ZX0^_8#s(ocQuqn`Pv-|$WO!=6@$%puGg{0L^sT+fwl-6fRH'
    'zMcz{?PCysrUh1b$N`6>nkZZctG2~jOl$Ashdpim96V>vUll&XyMztlZc@EZrE0`O2$`7w_C$~QiSC9KnKFx(u$)R`Nanv1CevOF'
    '>I@g7G6lt$P6#ntHPtDdgo^A9V=^1Vm`uqab~2!{fQU+kw!H&Wy_lHH$$!Bv@qQlAqn?zm&DoE9(C~Fjc*uBL!jWspnS33!_hw$B'
    'C>?kt`s7iw8-m*2&8zWevjw?kKVP7(?~irVH5;K25J=caMa9)6mJmkwnf{C+75*KA6#O%~%KT?=+3|1TeM>+{N6#7mWWN|Gay*fU'
    't|I-3UJVk#9^qdh?0wMRxLx7jv>OHDY%Jz+amOZx;=>$ME~Ok{_Uyqn#8i1;oobQ`8Lu&TZ>KYHm5RecIlFAmcPrQr_2gIcXBsb9'
    '{3BJod}LMV170tm*WRs(rQzP(+@hd$yiH>PP3BoN+}`bEcW%19A2Da}7^CahX8v^ZWwb)eH~Suz+F+@U^S8HS0as)Ro51jmqmOV$'
    'MjU7`iRT$a@ks%b9L^J+<8cBwE+sMtbOcD*93(M7F#wV5wi3ynWF$|<XS26(<Doo}3|ngl7HU7YeB0f5S@p3$<4F>*VS^T#sF$B-'
    'o7~?0=o*$Ka(+GK{Oy$UKc}3(pK|_DbFgY?+-x|!37*8uVcf?_WVlc3QODbtj!V0)ZWuQ(6B}kayi5w#3aalgyN^(%rV@c?%^=*m'
    'O)qW79etlv5RGJ2eT{Hkca3;Br=+U~+g{goOYlVVSzWi}Hp;h&-DaE&%@<|?ZIHfYBw6~lRZCj3(k-k!RZ=bw?{u^jWRAYD)e@Gh'
    ';v!d5T=L2rUabb2Nnl7^=kezo9*x$LMbKo1L8ob34K-6-B5Mhk-OG198p4{X@0>N|1xw#WYe`F%zN6NXmMn31?Ta}p$`i4C+Z#%g'
    'T}_-nTxD3`1DNjaqz&?3H4HB42@Cd)GnM;sX|!tVYO85!D254(j@qt`yMUejs159~3Kw^~gWnVmw%li`G1L$i7b*-31r-#I%)Lv_'
    'ux3)hpTcB0UxU%mf(3jEN|k#G<pMkfVnv;XsCG_)@r+F&nxfJ)g>g-q0P8XTE9p$$E8<uzVcFo=mUP-SN`~HY+T1q!h046+RQwZ8'
    'Ya~v0qS@~ECj_wl6l#NG;y>K_=n~^{#9+w|<1v>go~S4gA70)1Mx|FSdw`V?tMJ|Oj57tVgkzC)xSPCLzEr;*OS;Oxho`|j-8LpR'
    'Ymny0me<F>xB-$&F$!lv)M%u?N|zyXVl16W<&%`~>4VySNy)Dq5Fv2J;=u_ATYIP^`yob1z`wTPziC(0+eh41_FNtwgnhUcq6hiU'
    '<K5<^scYJ{WxT?45Jhd{0zvgbx2W&1Tg8gcop12B3~penBKUCu^SjrVL(*dh^F(tu*d2nm6uQRHa!XOnwzvm#)EQnl>u_nId>Ec$'
    'g)miTxJU3^g0ilMNFMy}g&Sm`X!(y9vlg#xQiJ*&DqUIY;zdDqZ!JOM@)~0Wm9MceloM6yn9BL$k{ip)n{JF%*WEOup+#JLV@ThA'
    'V^m#%V^G|KOOU(_$6&q@ClGwU$;7)R#rw)zbKFE-o$JIEO?}m{eR761*vE8fl=vfBm3bqqYsMwkR&!D_E}3<0IB}b}e8>6}QyyT_'
    'A>!m9nvaVM#QXj5dg+oBm=%vFg1Ze{ijsgh^ziv-JFdphQ?^3&$r^;j;L62Yi<oz+PuP?QD{5a|izaQnZH7(5I`;4RX6cFJ3|mx('
    'g51i5duJk98#^`lC)o_aO)aDeyIb=CL6{9oClp3{yKP}GSNiD$TvO-#J#58$rTRZV6l|OXzDO!m{h=7P#$#w&!4!nnI7OQkBSn=J'
    'ha$!b7r!S{aGGjTlvi^a6#@;R81z**g?BaHRzvY!fww=0`uUe1>R48v$m+vbeGXe5!JeJI76-55P_J>sN>ydJ<~Y_mKSqI>8S)Mt'
    '1e$np0ylN0=>bUMGu7|jh{S^`WG+gTb1ibrK;+`zkXF#8z(t9!)+VzNsw6j2DJM}B)9PZ`vK&^GyC#Ct5=9lNsxtj+KLVuBoYVo5'
    'J|HU2f6CJxeO^-@!iaO0@)Sj%lIT+qeaayYIR4s{5;G;ZZBKnEHG~@ZX6CcE69h%EN5fB-+NqzG;;}R9gqPH5z!J@4mVi7?3F4tj'
    'fM(|b$`FlF0(h7Rz^?9h*q9bD7-7R2SNwsHee7XJ97b^HX>PoXAXhgo@z;C&xZ*XAT)VQ4$r%dj#jY5;%qLW#yo|;0FgcZ(el;a0'
    'b5RwgNEh{_3S<gD0}(|fsYJ1`L?BeX!-y&a6rgH{Wjjph>QRZxMm#ZyD(XfHl<B%=R5Dc8)AA%z6zF86D1ge08q}4g0+cV6C%2$w'
    'nHj-lMQI6RJt?7FDu-lMOG<E~+6g(Spe~Wm>P19tCIh;HRH9Ojmo8Gx+R=(7+c)b*E0%6Cx3te%Z(T2{aV^WXndrJwR5BWaFRDZl'
    '(A9m2iD^;Qhbmb1ty!XmtZWvEw&3hvNBS`*26eHh0OeB}g`x$cE)zW$C|TtyZWV}@96jgj;?M$Ti(J51K*%6&8AMe@p%u<ZSrDpV'
    'HHuUWiWHYzBBcvKGuE0YO{0`cK$#W=pa@lMisDZNHXl+KerjA{wBr(0PYo@tia-@clq>)h2>s2D4^yAbC2?N(Dfutf)T^RTl6b`{'
    '3O*$&zg<=Aso*S$KEttq%LS%L{|sjOxsKDEx(UC+B?>fe9wVvphk88!W+8ej{ELDZhxd3eRR7*!`Aa^Y!?e#c@Z`BCzYL_f^-umV'
    'yUl2gOe@tF9h02It8;#33J@j2k3t>e-pB*CQiCU1!DgngnIvqa4VxLmMh>x=K5Qfu%Uq&PES5P%onS0;i#pMWImSQ!A5u#|0R'
)
DEFAULTS = {"minecraft:" + name: props
            for props, names in json.loads(zlib.decompress(base64.b85decode(_DATA)))
            for name in names}


def normalize(palette):
    while isinstance(palette, dict) and set(palette) == {""}:
        palette = palette[""]
    if isinstance(palette, dict) and "Name" in palette:
        return palette
    if isinstance(palette, str):
        name, properties = palette, {}
    elif isinstance(palette, dict):
        name = palette.get("id")
        properties = palette.get("properties", {})
    else:
        raise ValueError("Unsupported block palette entry: %r" % (palette,))
    if not isinstance(name, str) or not isinstance(properties, dict):
        raise ValueError("Invalid block palette entry: %r" % (palette,))
    if ":" not in name:
        name = "minecraft:" + name
    result = dict(DEFAULTS.get(name, {}))
    result.update(properties)
    return {"Name": name, "Properties": result}
