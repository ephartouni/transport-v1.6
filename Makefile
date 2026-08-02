
INCLUDE = -Iinclude
FF = f77
TRANSPORT_OBJECTS = bin/transport.o \
	bin/trm.o \
	bin/trin.o \
	bin/trsec.o \
	bin/ranport.o

BSHEET_OBJECTS = bin/bshcall.o \
	bin/bshm.o 

TRANSLIB = lib/libtransport.a

SOURCES = $(TRANSPORT_OBJECTS:.o=.f) bshcall.f bshm.f

all: bin/trns.exe bin/bsheet.exe

FFLAGS = -g

bin/trns.exe : bin/trcall.o $(TRANSPORT_OBJECTS)
	$(FF) -o $@ bin/trcall.o $(TRANSPORT_OBJECTS)

bin/trcall.o: src/trcall.f
	$(FF) -o $@ $(FFLAGS) $(INCLUDE) -c src/trcall.f

bin/transport.o: src/transport.f
	$(FF) -o $@ $(FFLAGS) $(INCLUDE) -c src/transport.f

bin/trm.o: src/trm.f
	$(FF) -o $@ $(FFLAGS) $(INCLUDE) -c src/trm.f

bin/trin.o: src/trin.f
	$(FF) -o $@ $(FFLAGS) $(INCLUDE) -c src/trin.f

bin/trsec.o: src/trsec.f
	$(FF) -o $@ $(FFLAGS) $(INCLUDE) -c src/trsec.f

bin/ranport.o: src/ranport.f
	$(FF) -o $@ $(FFLAGS) $(INCLUDE) -c src/ranport.f

bin/ranibm.o: src/ranibm.f
	$(FF) -o $@ $(FFLAGS) $(INCLUDE) -c src/ranibm.f

bin/bsheet.exe: $(TRANSLIB) $(BSHEET_OBJECTS)
	$(FF) $(LFLAGS) -o $@ $(BSHEET_OBJECTS) -Llib -ltransport

bin/bshcall.o: src/bshcall.f
	$(FF) -o $@ $(FFLAGS) $(INCLUDE) -c src/bshcall.f

bin/bshm.o: src/bshm.f
	$(FF) -o $@ $(FFLAGS) $(INCLUDE) -c src/bshm.f

bin/trplot.o: src/trplot.f
	$(FF) -o $@ $(FFLAGS) -c -C src/trplot.f

bin/trplot.exe: bin/trplot.o
	$(FF) -o $@ bin/trplot.o

$(TRANSLIB) : $(TRANSPORT_OBJECTS)
	ar rs $(TRANSLIB) $(TRANSPORT_OBJECTS)

clean: 
	rm -f $(TRANSLIB)
	rm -f bin/*.o
	rm -f bin/*~*
	rm -f bin/trns.exe
	rm -f bin/bsheet.exe

