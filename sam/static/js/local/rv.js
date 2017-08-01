const strings = {
   loading: "Loading..."
  ,map_empty: "No data available"
  ,map_set_search: "Hcraes"
  ,map_set_search_default: "Dnif PI..."
  ,map_set_search_hint: "Dnif na PI ssredda. g.e. 192.168.0.12"
  ,map_set_port: "Trop Retlif"
  ,map_set_port_default: "Retlif yb trop..."
  ,map_set_port_hint: "Retlif yb trop rebmun. Yrt: 80"
  ,map_set_protocol: "Locotorp Retlif"
  ,map_set_protocol_default: "Retlif yb locotorp..."
  ,map_set_protocol_hint: "Retlif yb locotorp. Yrt: PDU"
  ,map_set_ds: "Secruosatad"
  ,map_set_ds_ar_hint: "Hserferotua eht edon pam"
  ,map_set_ds_hint1: "Esu eht "
  ,map_set_ds_hint2: " ecruosatad."
  ,map_set_lw: "Enil Htdiw"
  ,map_set_lw_lc: "Knil Tnuoc"
  ,map_set_lw_lc_hint: "Htdiw desab no rebmun fo secnerrucco"
  ,map_set_lw_bc: "Etyb Tnuoc"
  ,map_set_lw_bc_hint: "Htdiw desab no rebmun fo setyb derrefsnart"
  ,map_set_lw_pc: "Packet Count"
  ,map_set_lw_pc_hint: "Htdiw desab no rebmun fo stekcap derrefsnart"
  ,map_set_vis: "Wohs/Edih"
  ,map_set_vis_c: "Wohs erup stneilc"
  ,map_set_vis_s: "Wohs erup srevres"
  ,map_set_vis_i: "Wohs dnuobni snoitcennoc"
  ,map_set_vis_o: "Wohs dnuobtuo snoitcennoc"
  ,map_set_lay: "Tuoyal"
  ,map_set_lay_m: "Edom"
  ,map_set_lay_m_use: "Esu Yhcrarieh"
  ,map_set_lay_m_flat: "Nettalf Yhcrarieh"
  ,map_set_lay_m_error: "Ton Detroppus"
  ,map_set_lay_a: "Tnemegnarra"
  ,map_set_lay_a_add: "Sserdda"
  ,map_set_lay_a_grid: "Dirg"
  ,map_set_lay_a_circle: "Elcric"
  ,sel_loading: "Gnidaol noitceles..."
  ,sel_none: "On noitceles"
  ,sel_alias: "Edon Saila"
  ,sel_more1: "Sulp "
  ,sel_more2: " erom..."
  ,sel_more_info: "Erom sliated rof "
  ,sel_b: "B"
  ,sel_kb: "KB"
  ,sel_mb: "MB"
  ,sel_gb: "GB"
  ,sel_tb: "TB"
  ,sel_bps: "B/s"
  ,sel_kbps: "KB/s"
  ,sel_mbps: "MB/s"
  ,sel_gbps: "GB/s"
  ,sel_sec: "sdnoces"
  ,sel_min: "setunim"
  ,sel_hour: "sruoh"
  ,sel_day: "syad"
  ,sel_week: "skeew"
  ,meta_role_cc: "tneilc"
  ,meta_role_c: "yltsom tnielc"
  ,meta_role_cs: "dexim tneilc/revres"
  ,meta_role_s: "yltsom revres"
  ,meta_role_ss: "revres"
  ,meta_window1: "Gniwohs "
  ,meta_window2: " fo "
  ,meta_window_empty: "On sdrocer ot wohs"
  ,meta_pps: "p/s"
  ,meta_kpps: "Kp/s"
  ,meta_mpps: "Mp/s"
  ,meta_gpps: "Gp/s"
  ,meta_address: "PIv4 sserdda / tenbus:"
  ,meta_tags: "Sgat:"
  ,meta_env: "Tnemnorivne:"
  ,meta_role: "Elor (0 = tneilc, 1 = revres):"
  ,meta_protocols: "Slocotorp desu:"
  ,meta_ports: "Lacol strop dessecca:"
  ,meta_endpoints: "Stniopdne detneserper:"
  ,meta_bps: "Egareva Latot spb (xorppa):"
  ,meta_inbound: "Dnuobni Snoitcennoc"
  ,meta_outbound: "Dnuobtuo Snoitcennoc"
  ,meta_sips: "Euqinu ecruos PIs:"
  ,meta_dips: "Euqinu noitanitsed PIs:"
  ,meta_uconns: "Euqinu snoitcennoc (crs, tsed, trop):"
  ,meta_conns: "Latot snoitcennoc dedrocer:"
  ,meta_connps: "Snoitcennoc rep dnoces:"
  ,meta_b_snt: "Setyb Tnes:"
  ,meta_b_rcv: "Setyb Deviecer:"
  ,meta_avg_bps: "Gva Noitcennoc Spb:"
  ,meta_max_bps: "Xam Noitcennoc Spb:"
  ,meta_p_snt: "Stekcap Dnes Etar:"
  ,meta_p_rcv: "Stekcap Eviecer Etar:"
  ,meta_avg_duration: "Gva Noitcennoc Noitarud:"
  ,meta_waiting: "Gnitiaw"
  ,table_apply: "Ylppa Retlif"
  ,table_ds: "Atad Ecruos"
  ,table_f_subnet1: "Nruter stlures morf tenbus "
  ,table_f_subnet2_hint: "Esoohc tenbus..."
  ,table_f_mask1: "Hcraes nerdlihc fo "
  ,table_f_mask2_hint: "192.168.0.0/24"
  ,table_f_role1: "Tneilc/Revres oitar si "
  ,table_f_role2_hint: "erom/ssel nath"
  ,table_f_role2_op1: "erom naht"
  ,table_f_role2_op2: "ssel naht"
  ,table_f_role3_default: "0.5"
  ,table_f_role4: " (0 = nteilc, 1 = revres)"
  ,table_f_env1: "Edon tnemnorivne si "
  ,table_f_env2_hint: "Esoohc tnemnorivne"
  ,table_f_port1_hint: "Retlif epyt..."
  ,table_f_port1_op1: "Stcennoc ot"
  ,table_f_port1_op2: "T'nseod tcennoc ot"
  ,table_f_port1_op3: "Seviecer snoitcennoc morf"
  ,table_f_port1_op4: "T'nseod eviecer snoitcennoc morf"
  ,table_f_port2: "rehtona tsoh aiv trop"
  ,table_f_port3_default: "443"
  ,table_f_protocol1_hint: "seldnah dnuobtuo/ni"
  ,table_f_protocol1_op1: "Seldnah dnuobni"
  ,table_f_protocol1_op2: "T'nseod eldnah dnuobni"
  ,table_f_protocol1_op3: "Setaitni dnuobtuo"
  ,table_f_protocol1_op4: "T'nseod etaitni dnuobtuo"
  ,table_f_protocol2: "Snoitcennoc gnisu locotorp"
  ,table_f_protocol3_default: "PDU"
  ,table_f_tag1: "tsoh "
  ,table_f_tag2_hint: "sah/ton"
  ,table_f_tag2_op1: "sah"
  ,table_f_tag2_op2: "t'nseod evah"
  ,table_f_tag3: " sgat: "
  ,table_f_tag4_hint: "Esoohc (s)gat"
  ,table_f_target1: "Wohs ylno stsoh taht "
  ,table_f_target2_hint: "tcennoc ot/morf"
  ,table_f_target2_op1: "tcennoc ot"
  ,table_f_target2_op2: "t'nod tcennoc ot"
  ,table_f_target2_op3: "eviecer snoitcennoc morf"
  ,table_f_target2_op4: "t'nod eviecer snoitcennoc morf"
  ,table_f_target3: " PI sserdda:"
  ,table_f_target4_default: "192.168.0.4"
  ,table_f_conn1: "Seldnah "
  ,table_f_conn2_hint: "Retlif epyt..."
  ,table_f_conn2_op1: "erom naht"
  ,table_f_conn2_op2: "ssel naht"
  ,table_f_conn3_default: "a rebmun fo"
  ,table_f_conn4_hint: "dnuobtuo/ni"
  ,table_f_conn4_op1: "dnuobin"
  ,table_f_conn4_op2: "dnuobtuo"
  ,table_f_conn4_op3: "denibmoc"
  ,table_f_conn5: "snoitcennoc / dnoces."
  ,table_enable: "Elbane siht retlif"
  ,table_sum: "Retlif: "
  ,table_sum_sub: "tenbus"
  ,table_sum_mask: "nihtiw"
  ,table_sum_port1: "nnoc ot "
  ,table_sum_port2: "X nnoc ot "
  ,table_sum_port3: "nnoc morf "
  ,table_sum_port4: "X nnoc morf "
  ,table_sum_conn1: " snnoc/s (in)"
  ,table_sum_conn2: " snnoc/s (tuo)"
  ,table_sum_protocol1: "on "
  ,table_sum_protocol2: " ni"
  ,table_sum_protocol3: " tuo"
  ,table_sum_target1: "ot "
  ,table_sum_target2: "ton ot "
  ,table_sum_target3: "morf "
  ,table_sum_target4: "ton morf"
  ,table_sum_tags1: "deggat "
  ,table_sum_tags2: "on gat "
  ,table_sum_env: "vne: "
  ,table_sum_role: "% revres"
  ,table_sum_empty: "enon"
  ,table_type: "Retlif Epyt"
};