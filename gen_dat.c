/*
 *   gen_dat.c  -- generate a *.dat file from a *.bin file
 *
 *   Compile:  gcc gen_dat.c -o gen_dat
 *   NOTE:     move executable to app's gcc directory.
 */
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <errno.h>

/*
 *  Minimalistic INIT file structure
 *  See Nordic docs for INIT (*.dat) file format details.
 */
typedef struct {
    uint16_t device_type;
    uint16_t device_rev;
    uint32_t app_version;
    uint16_t softdevice_len;
    uint16_t softdevice_1;
    uint16_t softdevice_2;
    uint16_t crc;
} dfu_init_t;

static dfu_init_t dfu_init = {
    .device_type    = 0xffff,
    .device_rev     = 0xffff,
    .app_version    = 0xffffffff,
    .softdevice_len = 0x0002,
    .softdevice_1   = 0x005a,  // SoftDevice 7.1
    .softdevice_2   = 0x0064,  // SoftDevice 8.0
    .crc            = 0x0000,
};

/*
 *  This CRC code was liberated from the Nordic SDK.
 *  That way it exactly matched the algrithm used by the bootloader.
 */
uint16_t crc16_compute(const uint8_t * p_data,
                       uint32_t size,
                       const uint16_t * p_crc)
{
    uint32_t i;
    uint16_t crc = (p_crc == NULL) ? 0xffff : *p_crc;

    for (i = 0; i < size; i++) {
        crc  = (unsigned char)(crc >> 8) | (crc << 8);
        crc ^= p_data[i];
        crc ^= (unsigned char)(crc & 0xff) >> 4;
        crc ^= (crc << 8) << 4;
        crc ^= ((crc & 0xff) << 4) << 1;
    }
    return crc;
}

/*
 *  Given an input bin file, generate a matching dat file.
 */
int main(int argc, char* argv[])
{
    char * binfilename = NULL;
    char * datfilename = NULL;

    FILE * binfile = NULL;
    FILE * datfile = NULL;

    size_t    binsize  = 0;
    uint8_t * bindata  = NULL;
    uint16_t  crc      = 0;

    /*
     *  USAGE:  gen_dat  bin-filename dat-filename
     */
    if (argc < 3)
        return -1;

    binfilename = argv[1];
    datfilename = argv[2];

    /* Open bin file for reads. */
    binfile = fopen(binfilename, "r");
    if (binfile == NULL) {
        fprintf(stderr, "bin file open failed: %s\n", strerror(errno));
        return -1;
    }

    /* Open dat file for writes. */
    datfile = fopen(datfilename, "wb");
    if (datfile == NULL) {
        fprintf(stderr, "dat file open failed: %s\n", strerror(errno));
        fclose(binfile);
        return -1;
    }

    /* Detrmine size of bin file in bytes. */
    fseek(binfile, 0L, SEEK_END);
    binsize = ftell(binfile);
    fseek(binfile, 0L, SEEK_SET);

    if (binsize == 0) {
        fprintf(stderr, "bin file size determination failed");
        fclose(datfile);
        fclose(binfile);
        return -1;
    }

    /* Allocate buffer to hold all of bin file. */
    bindata = (uint8_t*) malloc(binsize);
    if (bindata == NULL) {
        fprintf(stderr, "malloc failed");
        fclose(datfile);
        fclose(binfile);
        return -1;
    }

    /* Fill buffer with bin file data. */
    fread(bindata, binsize, 1, binfile);

    /* Compute CRC-16. */
    dfu_init.crc = crc16_compute(bindata, binsize, 0);

    /* 
     *  Write INIT file
     */
    fwrite(&dfu_init, sizeof(dfu_init_t), 1, datfile);

    /*
     *  Close all files
     */
    fclose(datfile);
    fclose(binfile);

    return 0;
}