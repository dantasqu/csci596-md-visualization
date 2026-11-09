/* MODIFIED */
#include <stdlib.h>
#include <string.h>

static int viz_enabled, viz_every=30, capture_stress;
static int atom_id[NEMAX];
static double virial[NMAX][9];
static FILE *viz_dump, *viz_csv;

static int env_int(const char *key, int fallback) {
  const char *s=getenv(key); return s ? atoi(s) : fallback;
}
static double env_real(const char *key, double fallback) {
  const char *s=getenv(key); return s ? atof(s) : fallback;
}
static void viz_fail(const char *message) {
  fprintf(stderr,"VISUALIZATION ERROR: %s\n",message);
  MPI_Abort(MPI_COMM_WORLD,2);
}
static void check_visualization_setup(void) {
  int size;
  MPI_Comm_size(MPI_COMM_WORLD,&size);
  if (size!=nproc) viz_fail("MPI process count must match pmd.h");
  viz_enabled=env_int("VIZ_ENABLE",1);
  viz_every=env_int("VIZ_OUTPUT_EVERY",30);
  if (viz_every<1) viz_fail("Output interval must be positive");
}
static int region_of(int i) {
  return r[i][0]+vid[0]*al[0] < al[0]*vproc[0]*0.5 ? 0 : 1;
}
static void initialize_hot_cold(void) {
  double local[10]={0}, total[10], target[2];
  target[0]=env_real("VIZ_HOT",1.5);
  target[1]=env_real("VIZ_COLD",0.5);
  if (target[0]<=0 || target[1]<=0) viz_fail("Temperatures must be positive");
  for (int i=0;i<n;i++) {
    int g=region_of(i), q=5*g;
    local[q]++;
    for (int a=0;a<3;a++) {
      local[q+1+a]+=rv[i][a];
      local[q+4]+=rv[i][a]*rv[i][a];
    }
  }
  MPI_Allreduce(local,total,10,MPI_DOUBLE,MPI_SUM,MPI_COMM_WORLD);
  for (int g=0;g<2;g++) {
    int q=5*g;
    double count=total[q], variance=total[q+4];
    if (count<2) viz_fail("Both spatial halves need at least two atoms");
    for (int a=0;a<3;a++) variance-=total[q+1+a]*total[q+1+a]/count;
    if (variance<=0) viz_fail("Cannot rescale zero thermal velocity");
    double scale=sqrt(3*count*target[g]/variance);
    for (int i=0;i<n;i++) if (region_of(i)==g)
      for (int a=0;a<3;a++) rv[i][a]=(rv[i][a]-total[q+1+a]/count)*scale;
  }
}
static void write_visualization(void) {
  enum {WIDTH=16};
  double *local=malloc((size_t)n*WIDTH*sizeof(double));
  int *counts=malloc((size_t)nproc*sizeof(int));
  int *offsets=malloc((size_t)nproc*sizeof(int));
  if (!local || !counts || !offsets) viz_fail("Allocation failed");
  for (int i=0;i<n;i++) {
    double *p=local+i*WIDTH, ke=0, tensor[9];
    p[0]=atom_id[i];
    for (int a=0;a<3;a++) {
      p[1+a]=r[i][a]+vid[a]*al[a];
      p[4+a]=rv[i][a];
      ke+=0.5*rv[i][a]*rv[i][a];
      for (int b=0;b<3;b++) tensor[3*a+b]=Density*(rv[i][a]*rv[i][b]+virial[i][3*a+b]);
    }
    p[7]=ke;
    p[8]=tensor[0]; p[9]=tensor[4]; p[10]=tensor[8];
    p[11]=tensor[1]; p[12]=tensor[2]; p[13]=tensor[5];
    p[14]=sid; p[15]=1;
  }
  int sendcount=n*WIDTH;
  MPI_Gather(&sendcount,1,MPI_INT,counts,1,MPI_INT,0,MPI_COMM_WORLD);
  double *all=NULL;
  if (sid==0) {
    offsets[0]=0;
    for (int j=1;j<nproc;j++) offsets[j]=offsets[j-1]+counts[j-1];
    if (offsets[nproc-1]+counts[nproc-1]!=nglob*WIDTH) viz_fail("Atom count changed");
    all=malloc((size_t)nglob*WIDTH*sizeof(double));
    if (!all) viz_fail("Gather allocation failed");
  }
  MPI_Gatherv(local,sendcount,MPI_DOUBLE,all,counts,offsets,MPI_DOUBLE,0,MPI_COMM_WORLD);
  if (sid==0) {
    double box[3], regions[2][5]={{0}}, ke=0, pressure=0;
    int *index=malloc((size_t)nglob*sizeof(int));
    if (!index) viz_fail("Identifier allocation failed");
    for (int i=0;i<nglob;i++) index[i]=-1;
    for (int a=0;a<3;a++) box[a]=al[a]*vproc[a];
    for (int i=0;i<nglob;i++) {
      int id=(int)all[i*WIDTH];
      if (id<1 || id>nglob || index[id-1]!=-1) viz_fail("Duplicate or invalid atom ID");
      index[id-1]=i;
    }
    fprintf(viz_dump,"ITEM: TIMESTEP\n%d\nITEM: NUMBER OF ATOMS\n%d\nITEM: BOX BOUNDS pp pp pp\n",stepCount,nglob);
    for (int a=0;a<3;a++) fprintf(viz_dump,"0 %.12g\n",box[a]);
    fprintf(viz_dump,"ITEM: ATOMS id type x y z vx vy vz ke sxx syy szz sxy sxz syz rank\n");
    for (int j=0;j<nglob;j++) {
      double *p=all+index[j]*WIDTH;
      int g=p[1]<box[0]*0.5 ? 0 : 1;
      regions[g][0]++;
      for (int a=0;a<3;a++) regions[g][1+a]+=p[4+a];
      regions[g][4]+=2*p[7];
      ke+=p[7]; pressure+=(p[8]+p[9]+p[10])/3;
      fprintf(viz_dump,"%d 1",j+1);
      for (int q=1;q<=13;q++) fprintf(viz_dump," %.12g",p[q]);
      fprintf(viz_dump," %d\n",(int)p[14]);
    }
    double temps[2];
    for (int g=0;g<2;g++) {
      double variance=regions[g][4];
      for (int a=0;a<3;a++) variance-=regions[g][1+a]*regions[g][1+a]/regions[g][0];
      temps[g]=variance/(3*regions[g][0]);
    }
    fprintf(viz_csv,"%d,%.12g,%d,%.12g,%.12g,%.12g,%.12g,%.12g,%.12g,%.12g,%.12g,%.12g,%d,%d\n",
      stepCount,stepCount*DeltaT,nglob,temps[0],temps[1],2*ke/(3*nglob),potEnergy/nglob,(potEnergy+ke)/nglob,
      regions[0][1]+regions[1][1],regions[0][2]+regions[1][2],regions[0][3]+regions[1][3],pressure/nglob,
      (int)regions[0][0],(int)regions[1][0]);
    fflush(viz_csv); fflush(viz_dump);
    free(index); free(all);
  }
  free(local); free(counts); free(offsets);
}
static void prepare_visualization(void) {
  if (!viz_enabled) return;
  for (int a=0;a<3;a++) if (al[a]<2*RCUT) viz_fail("Each MPI subdomain must span at least two cutoffs");
  int warmup=env_int("VIZ_WARMUP",2000);
  if (warmup<0) viz_fail("Warmup cannot be negative");
  for (int k=0;k<warmup;k++) single_step();
  initialize_hot_cold();
  stepCount=0;
  capture_stress=1;
  atom_copy(); compute_accel();
  if (sid==0) {
    viz_dump=fopen("trajectory.dump","w");
    viz_csv=fopen("thermo.csv","w");
    if (!viz_dump || !viz_csv) viz_fail("Cannot open output files");
    fprintf(viz_csv,"step,time,N,T_left,T_right,T_global,E_potential,E_total,Px,Py,Pz,pressure,N_left,N_right\n");
    printf("VIZ: %d ranks; warmup=%d; hot=%.6g; cold=%.6g; frames every %d steps\n",nproc,warmup,env_real("VIZ_HOT",1.5),env_real("VIZ_COLD",0.5),viz_every);
  }
  write_visualization();
}
static void close_visualization(void) {
  if (sid==0 && viz_enabled) {fclose(viz_dump); fclose(viz_csv);}
}
/* END MODIFIED */
