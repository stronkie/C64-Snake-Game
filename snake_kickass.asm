// =============================================================
//  SNAKE for the Commodore 64
//  Assembler: KickAssembler
//  Build:     java -jar KickAss.jar snake.asm
//  Run:       x64sc snake.prg
//
//  Controls:  Joystick in port 2, or W A S D on the keyboard
// =============================================================

// ---------- hardware addresses ----------
.const SCREEN    = $0400        // screen memory (40x25 chars)
.const COLOR     = $d800        // color memory
.const RASTER    = $d012        // current raster line
.const JOY2      = $dc00        // joystick port 2
.const GETIN     = $ffe4        // kernal: read a key from buffer
.const CLRSCR    = $e544        // kernal: clear the screen

// ---------- screen codes ----------
.const CHR_SPACE = $20
.const CHR_WALL  = $a0          // solid block (reversed space)
.const CHR_BODY  = $51          // filled circle
.const CHR_APPLE = $53          // heart

// ---------- colors ----------
.const COL_BLACK = 0
.const COL_WHITE = 1
.const COL_RED   = 2
.const COL_GREEN = 5
.const COL_WALL  = 12           // medium grey

// ---------- directions ----------
// Opposite directions differ only in bit 0, so (dir XOR 1)
// gives the opposite direction. Handy for blocking reversals.
.const DIR_RIGHT = 0
.const DIR_LEFT  = 1
.const DIR_DOWN  = 2
.const DIR_UP    = 3

// ---------- game settings ----------
.const SPEED     = 6            // frames per step (lower = faster)
.const START_LEN = 4

// ---------- zero page pointers ----------
.const ptr       = $fb          // $fb/$fc -> screen position
.const cptr      = $fd          // $fd/$fe -> matching color position

// ---------- snake body buffer ----------
// A ring buffer of 256 X and 256 Y positions.
// headidx points at the head, tailidx at the tail end.
// Because the indexes are bytes, they wrap around for free.
.label bodyX     = $3000
.label bodyY     = $3100

// =============================================================
BasicUpstart2(start)            // creates "10 SYS 2064" for us

* = $0810 "Code"

start:
        lda #COL_BLACK
        sta $d020               // border
        sta $d021               // background

        // Set SID voice 3 to noise; reading $d41b then gives
        // us random numbers for apple placement.
        lda #$ff
        sta $d40e
        sta $d40f
        lda #$80
        sta $d412

newgame:
        jsr CLRSCR
        jsr drawscoreline
        jsr drawwalls
        jsr initsnake
        jsr showscore
        jsr placeapple

// =============================================================
//  MAIN LOOP: wait, move the snake one step, repeat
// =============================================================
mainloop:
        jsr waitframes          // wait SPEED frames, reading input

        lda newdir              // commit the requested direction
        sta dir

        // work out where the head goes next
        lda headx
        sta newx
        lda heady
        sta newy

        lda dir
        bne notright
        inc newx
        jmp moved
notright:
        cmp #DIR_LEFT
        bne notleft
        dec newx
        jmp moved
notleft:
        cmp #DIR_DOWN
        bne notdown
        inc newy
        jmp moved
notdown:
        dec newy

moved:
        lda #0
        sta ate

        // look at what is on the screen where the head will go
        lda newx
        sta px
        lda newy
        sta py
        jsr setptr
        ldy #0
        lda (ptr),y
        cmp #CHR_APPLE
        beq ateapple

        // No apple: the tail moves forward. We erase the tail
        // BEFORE the collision check so the head may move into
        // the square the tail just left.
        jsr erasetail
        lda newx
        sta px
        lda newy
        sta py
        jsr setptr
        ldy #0
        lda (ptr),y
        cmp #CHR_SPACE
        beq advance
        jmp gameover            // hit a wall or ourselves

ateapple:
        lda #1
        sta ate
        jsr addscore
        // The ring buffer holds 256 entries, so stop growing
        // when the snake gets close to that length.
        lda headidx
        sec
        sbc tailidx
        cmp #250
        bcc advance
        jsr erasetail

advance:
        // store the new head in the ring buffer and draw it
        inc headidx
        ldx headidx
        lda newx
        sta bodyX,x
        sta headx
        sta px
        lda newy
        sta bodyY,x
        sta heady
        sta py
        jsr setptr
        ldy #0
        lda #CHR_BODY
        sta (ptr),y
        lda #COL_GREEN
        sta (cptr),y

        lda ate
        beq nonewapple
        jsr placeapple
nonewapple:
        jmp mainloop

// =============================================================
//  GAME OVER
// =============================================================
gameover:
        ldx #0
!:      lda gameovertext,x
        cmp #$ff
        beq !+
        sta SCREEN+12*40+8,x
        lda #COL_WHITE
        sta COLOR+12*40+8,x
        inx
        jmp !-
!:
        // short pause so a held key doesn't restart instantly
        lda #50
        sta framecnt
!:      jsr wait1frame
        dec framecnt
        bne !-

waitrelease:
        lda JOY2
        and #%00010000          // fire button (0 = pressed)
        beq waitrelease
        lda #0
        sta $c6                 // empty the keyboard buffer

waitpress:
        lda JOY2
        and #%00010000
        beq restart
        jsr GETIN
        beq waitpress
restart:
        jmp newgame

// =============================================================
//  SUBROUTINES
// =============================================================

// ---- setptr: point ptr/cptr at screen position (px, py) ----
setptr:
        ldy py
        lda rowLo,y
        clc
        adc px
        sta ptr
        sta cptr
        lda rowHi,y
        adc #0
        sta ptr+1
        clc
        adc #>(COLOR-SCREEN)    // color RAM is $d400 above screen
        sta cptr+1
        rts

// ---- erasetail: blank the last body piece, move tail on ----
erasetail:
        ldx tailidx
        lda bodyX,x
        sta px
        lda bodyY,x
        sta py
        jsr setptr
        ldy #0
        lda #CHR_SPACE
        sta (ptr),y
        inc tailidx
        rts

// ---- placeapple: put an apple on a random empty square ----
placeapple:
randx:  lda $d41b               // random 0-255
        and #%00111111          // 0-63
        cmp #38
        bcs randx               // keep 0-37
        clc
        adc #1                  // x = 1-38
        sta px
randy:  lda $d41b
        and #%00011111          // 0-31
        cmp #22
        bcs randy               // keep 0-21
        clc
        adc #2                  // y = 2-23
        sta py
        jsr setptr
        ldy #0
        lda (ptr),y
        cmp #CHR_SPACE
        bne randx               // occupied, try again
        lda #CHR_APPLE
        sta (ptr),y
        lda #COL_RED
        sta (cptr),y
        rts

// ---- initsnake: reset variables and draw the starting snake ----
initsnake:
        lda #0
        sta tailidx
        sta scorelo
        sta scorehi
        lda #DIR_RIGHT
        sta dir
        sta newdir

        ldx #0
!:      txa
        clc
        adc #17                 // x = 17, 18, 19, 20
        sta bodyX,x
        sta px
        lda #12                 // y = 12 (middle row)
        sta bodyY,x
        sta py
        stx headidx
        jsr setptr              // uses A and Y only, X is safe
        ldy #0
        lda #CHR_BODY
        sta (ptr),y
        lda #COL_GREEN
        sta (cptr),y
        inx
        cpx #START_LEN
        bne !-

        lda px
        sta headx
        lda py
        sta heady
        rts

// ---- drawwalls: border around rows 1-24 ----
drawwalls:
        ldx #39
!:      lda #CHR_WALL
        sta SCREEN+1*40,x       // top wall
        sta SCREEN+24*40,x      // bottom wall
        lda #COL_WALL
        sta COLOR+1*40,x
        sta COLOR+24*40,x
        dex
        bpl !-

        lda #2
        sta py
!:      lda #0
        sta px
        jsr setptr
        ldy #0
        lda #CHR_WALL
        sta (ptr),y             // left wall
        ldy #39
        sta (ptr),y             // right wall
        lda #COL_WALL
        sta (cptr),y
        ldy #0
        sta (cptr),y
        inc py
        lda py
        cmp #24
        bne !-
        rts

// ---- drawscoreline: "SCORE 0000" on the top row ----
drawscoreline:
        ldx #0
!:      lda scoretext,x
        cmp #$ff
        beq !+
        sta SCREEN,x
        lda #COL_WHITE
        sta COLOR,x
        inx
        bne !-
!:      rts

// ---- addscore: add 1 to the 4-digit decimal (BCD) score ----
addscore:
        sei                     // the kernal IRQ doesn't expect
        sed                     // decimal mode, so block it
        clc
        lda scorelo
        adc #1
        sta scorelo
        lda scorehi
        adc #0
        sta scorehi
        cld
        cli
        // fall through to showscore

// ---- showscore: print the BCD score at column 6 ----
showscore:
        lda scorehi
        ldx #6
        jsr putbcd
        lda scorelo
        ldx #8
        // fall through: putbcd's rts returns from showscore
putbcd:
        pha
        lsr
        lsr
        lsr
        lsr
        ora #$30                // screen code for '0'
        sta SCREEN,x
        pla
        and #$0f
        ora #$30
        sta SCREEN+1,x
        rts

// ---- wait1frame: wait until the next frame ----
wait1frame:
!:      lda RASTER
        cmp #$fb
        bne !-
!:      lda RASTER
        cmp #$fb
        beq !-
        rts

// ---- waitframes: wait SPEED frames, checking input each frame ----
waitframes:
        lda #SPEED
        sta framecnt
wfloop: jsr wait1frame
        jsr readinput
        dec framecnt
        bne wfloop
        rts

// ---- readinput: joystick port 2, then W A S D ----
readinput:
        lda JOY2
        lsr                     // bit 0: up
        bcs !+
        ldx #DIR_UP
        jmp trydir
!:      lsr                     // bit 1: down
        bcs !+
        ldx #DIR_DOWN
        jmp trydir
!:      lsr                     // bit 2: left
        bcs !+
        ldx #DIR_LEFT
        jmp trydir
!:      lsr                     // bit 3: right
        bcs !+
        ldx #DIR_RIGHT
        jmp trydir

!:      jsr GETIN               // no joystick, try the keyboard
        cmp #$57                // W
        bne !+
        ldx #DIR_UP
        jmp trydir
!:      cmp #$53                // S
        bne !+
        ldx #DIR_DOWN
        jmp trydir
!:      cmp #$41                // A
        bne !+
        ldx #DIR_LEFT
        jmp trydir
!:      cmp #$44                // D
        bne !+
        ldx #DIR_RIGHT
        jmp trydir
!:      rts

// ---- trydir: accept direction X unless it reverses the snake ----
trydir:
        txa
        eor #1                  // opposite of requested direction
        cmp dir
        beq !+                  // would reverse into ourselves
        stx newdir
!:      rts

// =============================================================
//  DATA
// =============================================================

// start address of each screen row
rowLo:  .fill 25, <(SCREEN + i*40)
rowHi:  .fill 25, >(SCREEN + i*40)

.encoding "screencode_upper"
scoretext:    .text "SCORE 0000"
              .byte $ff
gameovertext: .text "GAME OVER - FIRE OR KEY"
              .byte $ff

// variables
dir:      .byte 0
newdir:   .byte 0
headx:    .byte 0
heady:    .byte 0
newx:     .byte 0
newy:     .byte 0
px:       .byte 0
py:       .byte 0
headidx:  .byte 0
tailidx:  .byte 0
ate:      .byte 0
framecnt: .byte 0
scorelo:  .byte 0
scorehi:  .byte 0
