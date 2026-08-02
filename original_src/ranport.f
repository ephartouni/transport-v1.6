      DOUBLE PRECISION FUNCTION DLARAN( ISEED )
c
c  -- LAPACK auxiliary routine (version 2.0) --
c     Univ. of Tennessee, Univ. of California Berkeley, NAG Ltd.,
c     Courant Institute, Argonne National Lab, and Rice University
c     February 29, 1992
c
c     .. Array Arguments ..
      INTEGER            ISEED( 4 )
c     ..
c
c  Purpose
c  =======
c
c  DLARAN returns a random real number from a uniform (0,1)
c  distribution.
c
c  Arguments
c  =========
c
c  ISEED   (input/output) INTEGER array, dimension (4)
c          On entry, the seed of the random number generator; the array
c          elements must be between 0 and 4095, and ISEED(4) must be
c          odd.
c          On exit, the seed is updated.
c
c  Further Details
c  ===============
c
c  This routine uses a multiplicative congruential method with modulus
c  2**48 and multiplier 33952834046453 (see G.S.Fishman,
c  'Multiplicative congruential random number generators with modulus
c  2**b: an exhaustive analysis for b = 32 and a partial analysis for
c  b = 48', Math. Comp. 189, pp 331-344, 1990).
c
c  48-bit integers are stored in 4 integer array elements with 12 bits
c  per element. Hence the routine is portable across machines with
c  integers of 32 bits or more.
c
c  =====================================================================
c
c     .. Parameters ..
      INTEGER            M1, M2, M3, M4
      PARAMETER          ( M1 = 494, M2 = 322, M3 = 2508, M4 = 2549 )
      DOUBLE PRECISION   ONE
      PARAMETER          ( ONE = 1.0D+0 )
      INTEGER            IPW2
      DOUBLE PRECISION   R
      PARAMETER          ( IPW2 = 4096, R = ONE / IPW2 )
c     ..
c     .. Local Scalars ..
      INTEGER            IT1, IT2, IT3, IT4
c     ..
c     .. Intrinsic Functions ..
      INTRINSIC          DBLE, MOD
c     ..
c     .. Executable Statements ..
c
c     multiply the seed by the multiplier modulo 2**48
c
      IT4 = ISEED( 4 )*M4
      IT3 = IT4 / IPW2
      IT4 = IT4 - IPW2*IT3
      IT3 = IT3 + ISEED( 3 )*M4 + ISEED( 4 )*M3
      IT2 = IT3 / IPW2
      IT3 = IT3 - IPW2*IT2
      IT2 = IT2 + ISEED( 2 )*M4 + ISEED( 3 )*M3 + ISEED( 4 )*M2
      IT1 = IT2 / IPW2
      IT2 = IT2 - IPW2*IT1
      IT1 = IT1 + ISEED( 1 )*M4 + ISEED( 2 )*M3 + ISEED( 3 )*M2 +
     $      ISEED( 4 )*M1
      IT1 = MOD( IT1, IPW2 )
c
c     return updated seed
c
      ISEED( 1 ) = IT1
      ISEED( 2 ) = IT2
      ISEED( 3 ) = IT3
      ISEED( 4 ) = IT4
c
c     convert 48-bit integer to a real number in the interval (0,1)
c
      DLARAN = R*( DBLE( IT1 )+R*( DBLE( IT2 )+R*( DBLE( IT3 )+R*
     $         ( DBLE( IT4 ) ) ) ) )
      RETURN
c
c     End of DLARAN
c
      END
      FUNCTION RANDIS()
      COMMON /ISEED/   ISEED(4)
C
      RANDIS = 2.0*DLARAN(ISEED) - 1.0
      RETURN
      END
      SUBROUTINE RANGET(IGET)
      DIMENSION       IGET(4)
      COMMON /ISEED/  ISEED(4)
C
      DO 10 J = 1, 4
      IGET(J) = ISEED(J)
   10 CONTINUE
      RETURN
      END
      SUBROUTINE RANSET(IGET)
      DIMENSION       IGET(4)
      COMMON /ISEED/  ISEED(4)
C
      DO 10 J = 1, 4
      ISEED(J) = IGET(J)
   10 CONTINUE
      RETURN
      END
      SUBROUTINE RANST
      DIMENSION ISINIT(4)
      COMMON /ISEED/   ISEED(4)
      DATA ISINIT /0,0,0,1/
C
      DO 10 J = 1, 4
      ISEED(J) = ISINIT(J)
   10 CONTINUE
      RETURN
      END
      SUBROUTINE RCLOCK(ISET)
C
      XSET = 0.0
C     XSET = SECNDS(0.0)
      ISET = IFIX(100.0*XSET)
      ISET = (2*(ISET/2)) + 1
      RETURN
      END
