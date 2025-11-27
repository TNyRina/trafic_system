import { ComponentFixture, TestBed } from '@angular/core/testing';

import { Statistic } from './statistic';

describe('Statistic', () => {
  let component: Statistic;
  let fixture: ComponentFixture<Statistic>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [Statistic]
    })
    .compileComponents();

    fixture = TestBed.createComponent(Statistic);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
